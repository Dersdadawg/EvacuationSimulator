"""Matplotlib-based animation for the simulation - Modern UI"""

import matplotlib
matplotlib.use('TkAgg')  # Use interactive backend

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import numpy as np
from typing import Optional
from .wall_renderer import WallRenderer

# Modern corporate styling - Clean sans-serif
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Helvetica', 'Arial', 'DejaVu Sans', 'sans-serif']
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 15
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9


class MatplotlibAnimator:
    """Modern animated visualizer for evacuation simulation"""
    
    # Modern color palette - Material Design inspired
    COLORS = {
        'bg': '#FAFAFA',
        'white': '#FFFFFF',
        'grid': '#E0E0E0',
        'text_dark': '#212121',
        'text_light': '#757575',
        'primary': '#1976D2',
        'success': '#43A047',
        'warning': '#FB8C00',
        'danger': '#E53935',
        'office': '#E3F2FD',
        'hallway': '#F5F5F5',
        'exit': '#C8E6C9',
        'stair': '#BBDEFB',
        'agent_colors': ['#1976D2', '#F57C00', '#7B1FA2', '#00897B', 
                        '#C62828', '#5E35B1', '#D32F2F', '#00695C']
    }
    
    def __init__(self, simulator, fps=20):
        """Initialize modern animator"""
        self.sim = simulator
        self.fps = fps
        
        # Create figure with modern styling - LARGE SIZE
        self.fig = plt.figure(figsize=(22, 13), facecolor=self.COLORS['bg'])
        
        # Beautiful title with gradient-like effect
        title = self.fig.suptitle('EMERGENCY EVACUATION SIMULATOR', 
                         fontsize=24, fontweight='700', 
                         color='#1565C0', y=0.98,
                         bbox=dict(boxstyle='round,pad=0.8', 
                                  facecolor='white',
                                  edgecolor='#1976D2',
                                  linewidth=2.5,
                                  alpha=0.95))
        
        # Main plot area
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.COLORS['white'])
        
        # Setup plot with modern styling
        self.ax.set_aspect('equal')
        self.ax.set_xlabel('Position X (meters)', fontweight='500', 
                          color=self.COLORS['text_light'])
        self.ax.set_ylabel('Position Y (meters)', fontweight='500',
                          color=self.COLORS['text_light'])
        
        # Clean, minimal axes
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#E0E0E0')
        self.ax.spines['bottom'].set_color('#E0E0E0')
        self.ax.tick_params(colors=self.COLORS['text_light'])
        
        # Grid setup
        self.current_floor = 0
        self.grid_resolution = 0.5  # 0.5m x 0.5m grid
        
        # Initialize artists
        self.room_patches = {}
        self.room_labels = []
        self.priority_labels = []
        self.cell_heatmap_patches = []
        self.agent_dots = []
        self.evacuee_dots = []
        self.agent_trails = []
        self.grid_lines = []
        
        self._update_bounds()
        self._draw_cell_heatmap()  # Draw cell-level danger heatmap
        self._draw_rooms()
        
        # Draw walls with door openings
        layout_dict = self.sim.env.layout
        self.wall_renderer = WallRenderer(self.ax, layout_dict, self.current_floor)
        self.wall_renderer.draw_walls()
        
        self._add_fire_legend()  # Add colorbar legend
        
        # Agent trail history
        self.trail_length = 30
        self.agent_positions = {i: [] for i in range(len(self.sim.agent_manager.agents))}
        
        # Modern info panel
        info_bbox = dict(boxstyle='round,pad=1.0', facecolor=self.COLORS['white'], 
                        edgecolor='#E0E0E0', linewidth=2, alpha=0.98)
        self.info_text = self.ax.text(0.02, 0.98, '', transform=self.ax.transAxes,
                                     verticalalignment='top', fontsize=10,
                                     fontfamily='sans-serif', color=self.COLORS['text_dark'],
                                     bbox=info_bbox, linespacing=1.6)
        
        # Animation state
        self.paused = True
        self.speed = 1.0  # Speed multiplier (0.1 to 5.0)
        self.step_accumulator = 0.0  # For fractional speed handling
        self.anim = None
        
        # Connect keyboard events
        self.fig.canvas.mpl_connect('key_press_event', self._on_key)
        
    def _update_bounds(self):
        """Update plot bounds and draw grid"""
        if self.current_floor in self.sim.env.bounds:
            x_min, y_min, x_max, y_max = self.sim.env.bounds[self.current_floor]
            self.ax.set_xlim(x_min, x_max)
            self.ax.set_ylim(y_min, y_max)
            self.ax.invert_yaxis()
            self._draw_grid(x_min, y_min, x_max, y_max)
    
    def _draw_grid(self, x_min, y_min, x_max, y_max):
        """Draw visible 0.5m x 0.5m grid overlay"""
        # Clear previous grid
        for line in self.grid_lines:
            line.remove()
        self.grid_lines = []
        
        # Vertical lines every 0.5m - MORE VISIBLE
        x = x_min
        while x <= x_max:
            line = self.ax.axvline(x, color=self.COLORS['grid'], 
                                   linewidth=0.5, alpha=0.35, zorder=0)
            self.grid_lines.append(line)
            x += self.grid_resolution
        
        # Horizontal lines every 0.5m - MORE VISIBLE
        y = y_min
        while y <= y_max:
            line = self.ax.axhline(y, color=self.COLORS['grid'], 
                                   linewidth=0.5, alpha=0.35, zorder=0)
            self.grid_lines.append(line)
            y += self.grid_resolution
    
    def _add_fire_legend(self):
        """Add fire danger colorbar legend"""
        # Create legend showing white -> red gradient
        legend_text = self.ax.text(
            0.98, 0.50, 
            'DANGER LEVEL\n'
            '━━━━━━━━━━━\n'
            'RED = FIRE\n'
            'Orange = High\n'
            'Yellow = Moderate\n'
            'White = Safe',
            transform=self.ax.transAxes,
            ha='right', va='center',
            fontsize=11, fontweight='600',
            fontfamily='sans-serif',
            color=self.COLORS['text_dark'],
            bbox=dict(boxstyle='round,pad=1.0', 
                     facecolor=self.COLORS['white'], 
                     edgecolor=self.COLORS['danger'], 
                     linewidth=2.5, alpha=0.95),
            zorder=100
        )
    
    def _draw_cell_heatmap(self):
        """Draw cell-level danger heatmap (white = safe, RED = FIRE!)"""
        # Clear previous heatmap
        for patch in self.cell_heatmap_patches:
            patch.remove()
        self.cell_heatmap_patches = []
        
        # Get cells from grid hazard system
        if hasattr(self.sim.env.hazard_system, 'cells'):
            cells = self.sim.env.hazard_system.cells
            
            # Debug: Print fire info
            burning = sum(1 for c in cells.values() if c.is_burning)
            drawn_count = 0
            
            for (x, y), cell in cells.items():
                # Check if cell is on current floor
                room_at_cell = self.sim.env.rooms.get(cell.room_id)
                if not room_at_cell or room_at_cell.floor != self.current_floor:
                    continue
                
                # WHITE -> RED COLORMAP with SHADERS
                if cell.is_burning:
                    # BURNING = BRIGHT RED with pulsing glow effect
                    # Add subtle animation based on burn time
                    pulse = 0.9 + 0.1 * (self.sim.tick % 10) / 10.0
                    
                    # Glow layer (larger, semi-transparent)
                    glow_size = self.grid_resolution * 1.3
                    glow = patches.Rectangle(
                        (x - glow_size/2, y - glow_size/2),
                        glow_size,
                        glow_size,
                        facecolor='#FF6600',  # Orange glow
                        edgecolor='none',
                        alpha=0.3 * pulse,
                        zorder=9
                    )
                    self.cell_heatmap_patches.append(glow)
                    self.ax.add_patch(glow)
                    
                    # Core fire (bright red)
                    color = '#FF0000'
                    alpha = 1.0
                    edge_glow = '#FFAA00'  # Yellow-orange edge
                    draw_it = True
                elif cell.danger_level > 0.001:
                    # Smooth danger gradient with shader
                    d = cell.danger_level
                    if d < 0.25:
                        # White -> Pale yellow
                        r, g, b = 1.0, 1.0, 0.95 - d * 0.6
                    elif d < 0.5:
                        # Yellow -> Orange
                        r, g, b = 1.0, 0.95 - (d - 0.25) * 2.0, 0.0
                    elif d < 0.75:
                        # Orange -> Red-orange
                        r, g, b = 1.0, 0.45 - (d - 0.5), 0.0
                    else:
                        # Red-orange -> Dark red
                        r, g, b = 0.9 + d * 0.1, 0.1 - d * 0.1, 0.0
                    
                    color = (r, g, b)
                    alpha = 0.5 + d * 0.5
                    edge_glow = None
                    draw_it = True
                else:
                    draw_it = False
                    edge_glow = None
                
                if draw_it:
                    drawn_count += 1
                    # Draw cell with shader effect
                    cell_size = self.grid_resolution
                    rect = patches.Rectangle(
                        (x - cell_size/2, y - cell_size/2),
                        cell_size,
                        cell_size,
                        facecolor=color,
                        edgecolor=edge_glow if edge_glow else 'none',
                        linewidth=0.5 if edge_glow else 0,
                        alpha=alpha,
                        zorder=10  # HIGH z-order - on TOP!
                    )
                    self.cell_heatmap_patches.append(rect)
                    self.ax.add_patch(rect)
            
            # Debug print
            if self.sim.tick % 20 == 0:  # Every 20 ticks
                print(f'[FIRE] Tick {self.sim.tick}: {burning} burning, {drawn_count} drawn, {len(self.cell_heatmap_patches)} patches')
        
    def _draw_rooms(self):
        """Draw rooms with modern, clean styling"""
        for room_id, room in self.sim.env.rooms.items():
            if room.floor != self.current_floor:
                continue
            
            # Determine room styling and fill
            # Calculate priority to check if P=0
            if not room.is_exit and not room.is_stair and hasattr(room, 'type') and room.type == 'office':
                if self.sim.agent_manager.agents:
                    first_agent = self.sim.agent_manager.agents[0]
                    priority = self.sim.decision_engine.calculate_priority_index(
                        room.id, first_agent.current_room
                    )
                else:
                    priority = 0
            else:
                priority = 1  # Non-offices don't get colored
            
            if priority == 0.0 or (room.cleared and room.evacuees_remaining == 0):
                # EVACUATED/ZERO PRIORITY ROOMS: LIGHT GREEN FILL
                edge_color = '#2E7D32'  # Dark green
                edge_width = 3.5
                facecolor = '#A5D6A7'  # Light green
                fill = True
                alpha = 0.7
            elif room.is_exit:
                edge_color = '#2E7D32'  # Dark green
                edge_width = 3.0
                facecolor = 'none'
                fill = False
                alpha = 1.0
            elif room.is_stair:
                edge_color = '#1565C0'  # Dark blue
                edge_width = 3.0
                facecolor = 'none'
                fill = False
                alpha = 1.0
            elif hasattr(room, 'type') and room.type == 'hallway':
                edge_color = '#616161'  # Dark gray
                edge_width = 2.5
                facecolor = 'none'
                fill = False
                alpha = 1.0
            else:
                edge_color = '#000000'  # BLACK borders for offices
                edge_width = 3.0
                facecolor = 'none'  # Transparent - show heatmap
                fill = False
                alpha = 1.0
            
            # Draw room rectangle
            rect = patches.Rectangle(
                (room.x1, room.y1),
                room.width,
                room.height,
                linewidth=edge_width,
                edgecolor=edge_color,
                facecolor=facecolor,
                fill=fill,
                alpha=alpha,
                zorder=15  # ABOVE heatmap (z=10)
            )
            self.room_patches[room_id] = rect
            self.ax.add_patch(rect)
            
            # Room label
            label_color = self.COLORS['success'] if room.is_exit else self.COLORS['text_dark']
            label_text = self.ax.text(room.x, room.y - 2, room.id,
                                     ha='center', va='center',
                                     fontsize=11, fontweight='600',
                                     fontfamily='sans-serif',
                                     color=label_color, zorder=2)
            self.room_labels.append(label_text)
            
            # Priority index (ONLY for offices - NOT hallway, exit, or stairs)
            if (not room.is_exit and not room.is_stair and 
                hasattr(room, 'type') and room.type == 'office'):
                # Calculate priority using first agent's position as reference
                if self.sim.agent_manager.agents:
                    first_agent = self.sim.agent_manager.agents[0]
                    priority = self.sim.decision_engine.calculate_priority_index(
                        room.id, first_agent.current_room
                    )
                    
                    # Display priority with modern styling
                    priority_text = self.ax.text(
                        room.x, room.y + 3, 
                        f'P = {priority:.1f}',
                        ha='center', va='center',
                        fontsize=11, fontweight='600',
                        fontfamily='sans-serif',
                        color=self.COLORS['primary'],
                        bbox=dict(boxstyle='round,pad=0.5', 
                                 facecolor='white', 
                                 edgecolor=self.COLORS['primary'], 
                                 linewidth=2, 
                                 alpha=0.95),
                        zorder=20  # Very high - always visible
                    )
                    self.priority_labels.append(priority_text)
    
    def _update_priority_labels(self):
        """Update priority index labels on OFFICES ONLY"""
        for room_id, room in self.sim.env.rooms.items():
            if room.floor != self.current_floor:
                continue
            # Only show priority for offices
            if room.is_exit or room.is_stair or (hasattr(room, 'type') and room.type != 'office'):
                continue
            
            # Calculate priority
            if self.sim.agent_manager.agents:
                first_agent = self.sim.agent_manager.agents[0]
                priority = self.sim.decision_engine.calculate_priority_index(
                    room.id, first_agent.current_room
                )
                
                # Display priority with modern styling
                priority_text = self.ax.text(
                    room.x, room.y + 2, 
                    f'P = {priority:.1f}',
                    ha='center', va='center',
                    fontsize=10, fontweight='500',
                    fontfamily='sans-serif',
                    color=self.COLORS['primary'],
                    bbox=dict(boxstyle='round,pad=0.4', 
                             facecolor='white', 
                             edgecolor=self.COLORS['primary'], 
                             linewidth=1.5, 
                             alpha=0.9),
                    zorder=3
                )
                self.priority_labels.append(priority_text)
    
    def _update_room_colors(self):
        """Update room colors based on hazard and status"""
        for room_id, room in self.sim.env.rooms.items():
            if room.floor != self.current_floor or room_id not in self.room_patches:
                continue
            
            rect = self.room_patches[room_id]
            hazard = room.hazard
            
            # Hazard gradient
            if hazard > 0.05:
                if hazard < 0.3:
                    color = '#FFF59D'  # Light yellow
                elif hazard < 0.6:
                    color = '#FFB74D'  # Orange
                else:
                    color = '#EF5350'  # Red
                rect.set_facecolor(color)
                rect.set_alpha(0.5 + hazard * 0.4)
            # Cleared rooms
            elif room.cleared:
                rect.set_facecolor('#A5D6A7')
                rect.set_alpha(0.6)
            # Default colors
            elif room.is_exit:
                rect.set_facecolor(self.COLORS['exit'])
                rect.set_alpha(0.7)
            elif room.is_stair:
                rect.set_facecolor(self.COLORS['stair'])
                rect.set_alpha(0.7)
            elif hasattr(room, 'type') and room.type == 'hallway':
                rect.set_facecolor(self.COLORS['hallway'])
                rect.set_alpha(0.7)
            else:
                rect.set_facecolor(self.COLORS['office'])
                rect.set_alpha(0.7)
    
    def _on_key(self, event):
        """Handle keyboard events"""
        if event.key == ' ':
            self.paused = not self.paused
        elif event.key == 'escape':
            plt.close(self.fig)
        elif event.key == 'up':
            self.current_floor = min(self.current_floor + 1, max(self.sim.env.floors.keys()))
            self._redraw_all()
        elif event.key == 'down':
            self.current_floor = max(self.current_floor - 1, min(self.sim.env.floors.keys()))
            self._redraw_all()
        elif event.key == 'j':
            # Slow down (0.1 intervals, min 0.1)
            self.speed = max(0.1, round(self.speed - 0.1, 1))
            print(f'Speed: {self.speed:.1f}x')
            # Update animation interval to reflect new speed
            if hasattr(self, 'anim') and self.anim:
                new_interval = (1000 / self.fps) / self.speed
                self.anim.event_source.interval = new_interval
        elif event.key == 'l':
            # Speed up (0.1 intervals, max 5.0)
            self.speed = min(5.0, round(self.speed + 0.1, 1))
            print(f'Speed: {self.speed:.1f}x')
            # Update animation interval to reflect new speed
            if hasattr(self, 'anim') and self.anim:
                new_interval = (1000 / self.fps) / self.speed
                self.anim.event_source.interval = new_interval
    
    def _redraw_all(self):
        """Redraw everything for floor changes"""
        self.ax.clear()
        self.ax.set_aspect('equal')
        self.ax.set_facecolor(self.COLORS['white'])
        self.ax.set_xlabel('Position X (meters)', fontweight='500', 
                          color=self.COLORS['text_light'])
        self.ax.set_ylabel('Position Y (meters)', fontweight='500',
                          color=self.COLORS['text_light'])
        
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.spines['left'].set_color('#E0E0E0')
        self.ax.spines['bottom'].set_color('#E0E0E0')
        self.ax.tick_params(colors=self.COLORS['text_light'])
        
        self._update_bounds()
        
        self.room_patches = {}
        self.room_labels = []
        self._draw_rooms()
        
        info_bbox = dict(boxstyle='round,pad=1.0', facecolor=self.COLORS['white'], 
                        edgecolor='#E0E0E0', linewidth=2, alpha=0.98)
        self.info_text = self.ax.text(0.02, 0.98, '', transform=self.ax.transAxes,
                                     verticalalignment='top', fontsize=10,
                                     fontfamily='sans-serif', color=self.COLORS['text_dark'],
                                     bbox=info_bbox, linespacing=1.6)
    
    def _update_frame(self, frame):
        """Update animation frame"""
        # Run simulation
        if not self.paused and not self.sim.complete:
            # Handle fractional speeds (0.1 to 5.0)
            self.step_accumulator += self.speed
            steps_to_take = int(self.step_accumulator)
            self.step_accumulator -= steps_to_take
            
            for _ in range(steps_to_take):
                if not self.sim.complete:
                    self.sim.step()
        
        # Clear dynamic elements
        for dot in self.agent_dots:
            dot.remove()
        for dot in self.evacuee_dots:
            dot.remove()
        for line in self.agent_trails:
            line.remove()
        
        self.agent_dots = []
        self.evacuee_dots = []
        self.agent_trails = []
        
        # Clear and redraw priority labels
        for label in self.priority_labels:
            label.remove()
        self.priority_labels = []
        
        # Update cell heatmap (MUST BE VISIBLE!)
        self._draw_cell_heatmap()
        
        # Redraw walls with door openings
        if hasattr(self, 'wall_renderer'):
            self.wall_renderer.draw_walls()
        
        # DON'T update room colors - keep transparent to show heatmap!
        
        # Update priority indices
        self._update_priority_labels()
        
        # Draw agents with modern styling
        for agent in self.sim.agent_manager.agents:
            if agent.floor != self.current_floor:
                continue
            
            color = self.COLORS['agent_colors'][agent.id % len(self.COLORS['agent_colors'])]
            
            # Update trail
            self.agent_positions[agent.id].append((agent.x, agent.y))
            if len(self.agent_positions[agent.id]) > self.trail_length:
                self.agent_positions[agent.id].pop(0)
            
            # Draw trail
            if len(self.agent_positions[agent.id]) > 1:
                trail = np.array(self.agent_positions[agent.id])
                line, = self.ax.plot(trail[:, 0], trail[:, 1], 
                                    color=color, alpha=0.3, 
                                    linewidth=2.5, solid_capstyle='round', 
                                    zorder=8)
                self.agent_trails.append(line)
            
            # Agent glow effect (larger, softer)
            outer_glow = patches.Circle((agent.x, agent.y), 1.8, 
                                       facecolor=color, alpha=0.1, 
                                       edgecolor='none', zorder=9)
            self.agent_dots.append(outer_glow)
            self.ax.add_patch(outer_glow)
            
            mid_glow = patches.Circle((agent.x, agent.y), 1.2, 
                                     facecolor=color, alpha=0.2, 
                                     edgecolor='none', zorder=9.5)
            self.agent_dots.append(mid_glow)
            self.ax.add_patch(mid_glow)
            
            # Agent body (with white border for contrast)
            body = patches.Circle((agent.x, agent.y), 0.9, 
                                 facecolor=color, 
                                 edgecolor='white',
                                 linewidth=2.5, zorder=10)
            self.agent_dots.append(body)
            self.ax.add_patch(body)
            
            # Show evacuee if carrying
            if agent.carrying_evacuee:
                # Draw evacuee icon overlapping agent
                evacuee_circle = patches.Circle((agent.x + 0.5, agent.y - 0.5), 0.5, 
                                               facecolor='#F44336',  # Red
                                               edgecolor='white',
                                               linewidth=2, zorder=11)
                self.agent_dots.append(evacuee_circle)
                self.ax.add_patch(evacuee_circle)
                
                # Small label
                evac_label = self.ax.text(agent.x + 0.5, agent.y - 0.5, '👤',
                                         ha='center', va='center',
                                         fontsize=8, zorder=12,
                                         color='white')
                self.agent_dots.append(evac_label)
            
            # Agent label or death marker
            if agent.is_dead:
                # Draw large red X over dead agent
                x_mark1 = self.ax.plot([agent.x - 1, agent.x + 1], 
                                      [agent.y - 1, agent.y + 1],
                                      color='#D32F2F', linewidth=4, zorder=12)[0]
                x_mark2 = self.ax.plot([agent.x - 1, agent.x + 1], 
                                      [agent.y + 1, agent.y - 1],
                                      color='#D32F2F', linewidth=4, zorder=12)[0]
                self.agent_dots.append(x_mark1)
                self.agent_dots.append(x_mark2)
                
                # Death label
                death_label = self.ax.text(
                    agent.x, agent.y - 2, 'DECEASED',
                    ha='center', va='center',
                    fontsize=9, fontweight='700',
                    fontfamily='sans-serif',
                    color='white', zorder=13,
                    bbox=dict(boxstyle='round,pad=0.4', 
                             facecolor='#D32F2F', 
                             edgecolor='none', alpha=0.95)
                )
                self.agent_dots.append(death_label)
            else:
                label = self.ax.text(agent.x, agent.y - 1.6, f'R{agent.id}',
                                   ha='center', va='center',
                                   fontsize=9, fontweight='600',
                                   fontfamily='sans-serif',
                                   color='white', zorder=11,
                                   bbox=dict(boxstyle='round,pad=0.3', 
                                            facecolor=color, 
                                            edgecolor='none', alpha=0.95))
                self.agent_dots.append(label)
        
        # Draw evacuees
        for room_id, room in self.sim.env.rooms.items():
            if room.floor != self.current_floor:
                continue
            if room.evacuees_remaining > 0:
                for i in range(room.evacuees_remaining):
                    offset_x = (i % 3 - 1) * 1.2
                    offset_y = (i // 3) * 1.2
                    
                    # Glow
                    glow = patches.Circle((room.x + offset_x, room.y + offset_y), 0.6,
                                         facecolor=self.COLORS['danger'], 
                                         alpha=0.15, edgecolor='none', zorder=5)
                    self.evacuee_dots.append(glow)
                    self.ax.add_patch(glow)
                    
                    # Body
                    person = patches.Circle((room.x + offset_x, room.y + offset_y), 0.4,
                                           facecolor=self.COLORS['danger'], 
                                           edgecolor='white',
                                           linewidth=1.2, zorder=6)
                    self.evacuee_dots.append(person)
                    self.ax.add_patch(person)
        
        # Update info panel with clean design
        results = self.sim.get_results()
        
        # Status
        if self.paused and self.sim.tick == 0:
            status = 'PAUSED - Press SPACE to start'
        elif self.paused:
            status = 'PAUSED'
        else:
            status = 'RUNNING'
        
        # Calculate percentages
        rescued_pct = (results['evacuees_rescued'] / results['total_evacuees'] * 100) \
                      if results['total_evacuees'] > 0 else 0
        cleared_pct = (results['rooms_cleared'] / results['total_rooms'] * 100) \
                      if results['total_rooms'] > 0 else 0
        
        # Format info panel
        info = (
            f"Time: {self.sim.time:.1f}s  |  Floor: {self.current_floor}  |  "
            f"Rescued: {results['evacuees_rescued']}/{results['total_evacuees']} ({rescued_pct:.0f}%)\n"
            f"Rooms Cleared: {results['rooms_cleared']}/{results['total_rooms']} ({cleared_pct:.0f}%)  |  "
            f"Score: {results['success_score']:.3f}  |  Speed: {self.speed:.1f}x\n"
            f"Status: {status}\n"
            f"{'─' * 60}\n"
            f"Controls: SPACE=Play/Pause  |  J/L=Speed  |  ESC=Quit"
        )
        
        if self.sim.complete:
            # Show end screen with full statistics
            self._show_end_screen(results)
            self.paused = True
        
        self.info_text.set_text(info)
        
        return self.agent_dots + self.evacuee_dots + self.agent_trails + [self.info_text]
    
    def _show_end_screen(self, results):
        """Display beautiful end screen with full statistics"""
        # Lower opacity of all background elements
        if not hasattr(self, '_end_screen_shown'):
            self._end_screen_shown = True
            
            # Dim all patches
            for patch in self.room_patches.values():
                patch.set_alpha(0.2)
            for patch in self.cell_heatmap_patches:
                patch.set_alpha(0.3)
            if hasattr(self, 'wall_renderer'):
                for patch in self.wall_renderer.wall_patches:
                    patch.set_alpha(0.2)
        
        # Determine outcome
        reason = 'complete'
        from ..engine.simulator import EventType
        for event in self.sim.events:
            if event.event_type == EventType.SIMULATION_END:
                reason = event.data.get('reason', 'complete')
                break
        
        if reason == 'all_rescued':
            title = 'MISSION SUCCESS'
            title_color = '#43A047'
            outcome = 'All evacuees rescued!'
        elif reason == 'all_agents_dead':
            title = 'MISSION FAILED'
            title_color = '#D32F2F'
            outcome = 'All responders deceased'
        else:
            title = 'TIME LIMIT'
            title_color = '#FB8C00'
            outcome = 'Time expired'
        
        # Calculate percentages
        rescued_pct = (results['evacuees_rescued'] / results['total_evacuees'] * 100) if results['total_evacuees'] > 0 else 0
        cleared_pct = (results['rooms_cleared'] / results['total_rooms'] * 100) if results['total_rooms'] > 0 else 0
        
        # Count deaths
        deaths = sum(1 for a in self.sim.agent_manager.agents if a.is_dead)
        
        # Beautiful end stats - remove emojis that cause font warnings
        stats = (
            f"{title}\n"
            f"{'═' * 50}\n"
            f"{outcome}\n\n"
            f"FINAL STATISTICS:\n"
            f"{'─' * 50}\n"
            f"Time Elapsed: {self.sim.time:.0f} seconds ({self.sim.time/60:.1f} minutes)\n"
            f"Evacuees Rescued: {results['evacuees_rescued']}/{results['total_evacuees']} ({rescued_pct:.0f}%)\n"
            f"Rooms Cleared: {results['rooms_cleared']}/{results['total_rooms']} ({cleared_pct:.0f}%)\n"
            f"Responders Lost: {deaths}/2\n"
            f"Max Fire Level: {results['max_hazard']:.0%}\n"
            f"Success Score: {results['success_score']:.3f}\n"
            f"{'═' * 50}\n\n"
            f"Press ESC to close"
        )
        
        # Large centered text box
        self.info_text.set_text(stats)
        self.info_text.set_fontsize(14)
        self.info_text.set_position((0.5, 0.5))
        self.info_text.set_horizontalalignment('center')
        self.info_text.set_verticalalignment('center')
        self.info_text.set_bbox(dict(boxstyle='round,pad=2.0', 
                                     facecolor='white', 
                                     edgecolor=title_color, 
                                     linewidth=5, 
                                     alpha=1.0))
        self.info_text.set_color(title_color)
        self.info_text.set_fontweight('700')
        self.info_text.set_zorder(1000)  # On top of everything!
    
    def run(self):
        """Start the animation"""
        # Calculate interval based on FPS and current speed
        interval = (1000 / self.fps) / self.speed
        
        self.anim = FuncAnimation(
            self.fig,
            self._update_frame,
            interval=interval,
            blit=False,
            cache_frame_data=False
        )
        
        plt.tight_layout()
        plt.show()
        
        return self.sim.get_results()
