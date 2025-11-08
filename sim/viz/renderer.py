"""Rendering engine for map and UI elements"""

import pygame
import math
from typing import Tuple, List, Optional
import numpy as np

from ..env.environment import Environment
from ..agents.agent_manager import AgentManager
from ..agents.agent import AgentState


class Renderer:
    """Renders the simulation view"""
    
    # Colors (colorblind-friendly palette)
    COLOR_BG = (245, 245, 245)
    COLOR_ROOM = (255, 255, 255)
    COLOR_ROOM_BORDER = (100, 100, 100)
    COLOR_CLEARED = (100, 200, 100)
    COLOR_EXIT = (50, 150, 50)
    COLOR_STAIR = (100, 150, 200)
    COLOR_EVACUEE = (220, 50, 50)
    COLOR_HAZARD_LOW = (255, 255, 200)
    COLOR_HAZARD_HIGH = (255, 100, 0)
    COLOR_AGENT = [(70, 130, 180), (220, 120, 50), (150, 80, 180), (50, 180, 130)]
    COLOR_TRAIL = (200, 200, 200)
    COLOR_TEXT = (30, 30, 30)
    COLOR_UI_BG = (230, 230, 230)
    COLOR_BUTTON = (200, 200, 200)
    COLOR_BUTTON_HOVER = (180, 180, 180)
    COLOR_BUTTON_ACTIVE = (150, 200, 150)
    
    def __init__(self, width: int, height: int):
        """
        Initialize renderer
        
        Args:
            width: Window width
            height: Window height
        """
        pygame.init()
        pygame.font.init()
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Emergency Building Sweep Simulator")
        
        # Fonts
        self.font_small = pygame.font.SysFont('arial', 14)
        self.font_medium = pygame.font.SysFont('arial', 18)
        self.font_large = pygame.font.SysFont('arial', 24, bold=True)
        
        # Layout areas
        self.map_rect = pygame.Rect(10, 10, width - 320, height - 120)
        self.control_rect = pygame.Rect(10, height - 100, width - 320, 90)
        self.info_rect = pygame.Rect(width - 300, 10, 290, height - 20)
        
        # View state
        self.current_floor = 0
        self.camera_offset = (0, 0)
        self.zoom = 1.0
        self.show_hazard = True
        self.show_trails = True
        self.show_evacuees = True
        
        # Event annotations
        self.annotations: List[dict] = []
        
        # Heatmap surface cache
        self.heatmap_surface = None
        self.heatmap_alpha = 0.6
    
    def clear(self):
        """Clear screen"""
        self.screen.fill(self.COLOR_BG)
    
    def render_map(self, env: Environment, agent_manager: AgentManager, tick: int):
        """
        Render the building map for current floor
        
        Args:
            env: Environment to render
            agent_manager: Agent manager
            tick: Current simulation tick
        """
        # Draw map background
        pygame.draw.rect(self.screen, (255, 255, 255), self.map_rect)
        pygame.draw.rect(self.screen, self.COLOR_ROOM_BORDER, self.map_rect, 2)
        
        # Calculate view transform
        if self.current_floor in env.bounds:
            x_min, y_min, x_max, y_max = env.bounds[self.current_floor]
            world_width = x_max - x_min
            world_height = y_max - y_min
            
            # Calculate scale to fit
            scale_x = self.map_rect.width / world_width if world_width > 0 else 1
            scale_y = self.map_rect.height / world_height if world_height > 0 else 1
            scale = min(scale_x, scale_y) * 0.9 * self.zoom
            
            offset_x = self.map_rect.x + self.map_rect.width / 2 - (x_min + x_max) / 2 * scale
            offset_y = self.map_rect.y + self.map_rect.height / 2 - (y_min + y_max) / 2 * scale
            
            def world_to_screen(x, y):
                sx = offset_x + x * scale
                sy = offset_y + y * scale
                return int(sx), int(sy)
            
            # Render hazard heatmap
            if self.show_hazard:
                self._render_hazard_heatmap(env, self.current_floor, world_to_screen, scale)
            
            # Render rooms
            for room_id in env.floors.get(self.current_floor, []):
                room = env.rooms[room_id]
                self._render_room(room, world_to_screen, scale)
            
            # Render connections (optional)
            # self._render_connections(env, self.current_floor, world_to_screen)
            
            # Render agent trails
            if self.show_trails:
                for agent in agent_manager.get_agents_on_floor(self.current_floor):
                    self._render_agent_trail(agent, world_to_screen)
            
            # Render agents
            for agent in agent_manager.get_agents_on_floor(self.current_floor):
                self._render_agent(agent, world_to_screen)
            
            # Render annotations
            self._render_annotations(tick, world_to_screen, env)
    
    def _render_room(self, room, world_to_screen, scale):
        """Render a single room"""
        x1, y1 = world_to_screen(room.x1, room.y1)
        x2, y2 = world_to_screen(room.x2, room.y2)
        
        w = x2 - x1
        h = y2 - y1
        
        rect = pygame.Rect(x1, y1, max(1, w), max(1, h))
        
        # Room fill color
        if room.is_exit:
            color = self.COLOR_EXIT
        elif room.is_stair:
            color = self.COLOR_STAIR
        elif room.cleared:
            color = self.COLOR_CLEARED
        else:
            color = self.COLOR_ROOM
        
        pygame.draw.rect(self.screen, color, rect)
        
        # Room border
        border_color = self.COLOR_ROOM_BORDER if not room.cleared else (50, 150, 50)
        border_width = 3 if room.cleared else 1
        pygame.draw.rect(self.screen, border_color, rect, border_width)
        
        # Room label
        if w > 30 and h > 20:
            cx, cy = world_to_screen(room.x, room.y)
            label = self.font_small.render(room.id, True, self.COLOR_TEXT)
            label_rect = label.get_rect(center=(cx, cy - 5))
            self.screen.blit(label, label_rect)
            
            # Show evacuees if discovered and present
            if self.show_evacuees and room.discovered_evacuees and room.evacuees_remaining > 0:
                evac_text = f"👤{room.evacuees_remaining}"
                evac_label = self.font_small.render(evac_text, True, self.COLOR_EVACUEE)
                evac_rect = evac_label.get_rect(center=(cx, cy + 8))
                self.screen.blit(evac_label, evac_rect)
    
    def _render_hazard_heatmap(self, env, floor, world_to_screen, scale):
        """Render hazard heatmap overlay"""
        for room_id in env.floors.get(floor, []):
            room = env.rooms[room_id]
            
            if room.hazard < 0.05:
                continue
            
            x1, y1 = world_to_screen(room.x1, room.y1)
            x2, y2 = world_to_screen(room.x2, room.y2)
            
            w = x2 - x1
            h = y2 - y1
            
            if w < 1 or h < 1:
                continue
            
            # Interpolate color based on hazard level
            t = room.hazard
            color = (
                int(self.COLOR_HAZARD_LOW[0] * (1-t) + self.COLOR_HAZARD_HIGH[0] * t),
                int(self.COLOR_HAZARD_LOW[1] * (1-t) + self.COLOR_HAZARD_HIGH[1] * t),
                int(self.COLOR_HAZARD_LOW[2] * (1-t) + self.COLOR_HAZARD_HIGH[2] * t),
            )
            
            # Create transparent overlay
            overlay = pygame.Surface((w, h))
            overlay.set_alpha(int(room.hazard * 180 * self.heatmap_alpha))
            overlay.fill(color)
            self.screen.blit(overlay, (x1, y1))
    
    def _render_agent(self, agent, world_to_screen):
        """Render an agent"""
        x, y = world_to_screen(agent.x, agent.y)
        
        # Agent color
        color = self.COLOR_AGENT[agent.id % len(self.COLOR_AGENT)]
        
        # Draw agent circle
        radius = 8
        pygame.draw.circle(self.screen, color, (x, y), radius)
        pygame.draw.circle(self.screen, (0, 0, 0), (x, y), radius, 2)
        
        # Draw directional indicator if moving
        if agent.state == AgentState.MOVING and agent.path:
            # Point toward next room
            next_idx = min(agent.path_index, len(agent.path) - 1)
            if next_idx < len(agent.path):
                from ..env.room import Room
                # Get current room to calculate direction
                pass  # Simplified: just show state
        
        # Agent ID label
        label = self.font_small.render(str(agent.id), True, (255, 255, 255))
        label_rect = label.get_rect(center=(x, y))
        self.screen.blit(label, label_rect)
        
        # State indicator
        state_colors = {
            AgentState.IDLE: (100, 100, 100),
            AgentState.MOVING: (100, 150, 255),
            AgentState.SEARCHING: (255, 200, 50),
            AgentState.DRAGGING: (255, 100, 100),
            AgentState.QUEUED: (150, 150, 150)
        }
        state_color = state_colors.get(agent.state, (128, 128, 128))
        pygame.draw.circle(self.screen, state_color, (x + radius - 2, y - radius + 2), 4)
    
    def _render_agent_trail(self, agent, world_to_screen):
        """Render agent movement trail"""
        trail = agent.get_trail(20)
        
        if len(trail) < 2:
            return
        
        points = [world_to_screen(x, y) for x, y, floor in trail if floor == agent.floor]
        
        if len(points) >= 2:
            pygame.draw.lines(self.screen, self.COLOR_TRAIL, False, points, 2)
    
    def _render_annotations(self, tick, world_to_screen, env):
        """Render event annotations"""
        # Filter expired annotations
        self.annotations = [a for a in self.annotations 
                           if tick - a['start_tick'] < a['duration']]
        
        for annot in self.annotations:
            if annot['room_id'] and annot['room_id'] in env.rooms:
                room = env.rooms[annot['room_id']]
                if room.floor == self.current_floor:
                    x, y = world_to_screen(room.x, room.y)
                    
                    # Fade out
                    age = tick - annot['start_tick']
                    alpha = 1.0 - (age / annot['duration'])
                    
                    text = annot['text']
                    color = tuple(int(c * alpha) for c in annot.get('color', (0, 0, 0)))
                    
                    label = self.font_medium.render(text, True, color)
                    label_rect = label.get_rect(center=(x, y - 20))
                    self.screen.blit(label, label_rect)
    
    def add_annotation(self, text: str, room_id: str, tick: int, 
                      duration: int = 60, color=(0, 0, 0)):
        """Add event annotation"""
        self.annotations.append({
            'text': text,
            'room_id': room_id,
            'start_tick': tick,
            'duration': duration,
            'color': color
        })
    
    def render_controls(self, paused: bool, speed: float, tick: int, time: float):
        """Render control panel"""
        pygame.draw.rect(self.screen, self.COLOR_UI_BG, self.control_rect)
        pygame.draw.rect(self.screen, self.COLOR_ROOM_BORDER, self.control_rect, 1)
        
        # Time display
        time_text = f"Tick: {tick}  Time: {time:.1f}s"
        time_label = self.font_medium.render(time_text, True, self.COLOR_TEXT)
        self.screen.blit(time_label, (self.control_rect.x + 10, self.control_rect.y + 10))
        
        # Status
        status = "PAUSED" if paused else f"RUNNING ({speed}x)"
        status_label = self.font_medium.render(status, True, self.COLOR_TEXT)
        self.screen.blit(status_label, (self.control_rect.x + 10, self.control_rect.y + 35))
        
        # Instructions
        instr = "SPACE:Play/Pause  →:Step  +/-:Speed  ↑↓:Floors  ESC:Quit"
        instr_label = self.font_small.render(instr, True, self.COLOR_TEXT)
        self.screen.blit(instr_label, (self.control_rect.x + 10, self.control_rect.y + 60))
    
    def render_info_panel(self, env: Environment, agent_manager: AgentManager, 
                         results: dict, tick: int):
        """Render information panel"""
        pygame.draw.rect(self.screen, self.COLOR_UI_BG, self.info_rect)
        pygame.draw.rect(self.screen, self.COLOR_ROOM_BORDER, self.info_rect, 1)
        
        y = self.info_rect.y + 10
        x = self.info_rect.x + 10
        line_height = 22
        
        # Title
        title = self.font_large.render("Live Metrics", True, self.COLOR_TEXT)
        self.screen.blit(title, (x, y))
        y += 35
        
        # Floor selector
        floor_text = f"Floor: {self.current_floor + 1}/{len(env.floors)}"
        floor_label = self.font_medium.render(floor_text, True, self.COLOR_TEXT)
        self.screen.blit(floor_label, (x, y))
        y += line_height + 5
        
        # Metrics
        metrics = [
            f"Rooms Cleared: {results['rooms_cleared']}/{results['total_rooms']} "
            f"({results['percent_cleared']:.0f}%)",
            f"Evacuees Rescued: {results['evacuees_rescued']}/{results['total_evacuees']} "
            f"({results['percent_rescued']:.0f}%)",
            f"Success Score: {results['success_score']:.3f}",
            f"Avg Hazard: {results['avg_hazard_exposure']:.2f}",
            f"Max Hazard: {results['max_hazard']:.2f}",
        ]
        
        for metric in metrics:
            label = self.font_small.render(metric, True, self.COLOR_TEXT)
            self.screen.blit(label, (x, y))
            y += line_height
        
        y += 10
        
        # Agent status
        agents_title = self.font_medium.render("Agents:", True, self.COLOR_TEXT)
        self.screen.blit(agents_title, (x, y))
        y += line_height
        
        for agent in agent_manager.agents:
            color = self.COLOR_AGENT[agent.id % len(self.COLOR_AGENT)]
            pygame.draw.circle(self.screen, color, (x + 8, y + 8), 6)
            
            agent_text = (f"A{agent.id}: {agent.state.value} "
                         f"(F{agent.floor + 1}, {agent.current_room})")
            label = self.font_small.render(agent_text, True, self.COLOR_TEXT)
            self.screen.blit(label, (x + 20, y))
            y += line_height
        
        y += 10
        
        # Legend
        legend_title = self.font_medium.render("Legend:", True, self.COLOR_TEXT)
        self.screen.blit(legend_title, (x, y))
        y += line_height
        
        legend_items = [
            ("Exit", self.COLOR_EXIT),
            ("Stair", self.COLOR_STAIR),
            ("Cleared", self.COLOR_CLEARED),
            ("Hazard", self.COLOR_HAZARD_HIGH),
        ]
        
        for label_text, color in legend_items:
            pygame.draw.rect(self.screen, color, (x, y, 15, 15))
            pygame.draw.rect(self.screen, (0, 0, 0), (x, y, 15, 15), 1)
            label = self.font_small.render(label_text, True, self.COLOR_TEXT)
            self.screen.blit(label, (x + 20, y))
            y += line_height
    
    def flip(self):
        """Update display"""
        pygame.display.flip()
    
    def capture_frame(self) -> pygame.Surface:
        """Capture current frame for video export"""
        return self.screen.copy()

