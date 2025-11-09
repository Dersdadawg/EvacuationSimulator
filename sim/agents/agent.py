"""Agent class representing firefighter behavior"""

from enum import Enum
from typing import List, Optional, Tuple
import numpy as np


class AgentState(Enum):
    """Agent states in the state machine"""
    IDLE = "idle"
    MOVING = "moving"
    SEARCHING = "searching"
    RESCUING = "rescuing"
    DRAGGING = "dragging"
    QUEUED = "queued"


class Agent:
    """Represents a firefighter agent"""
    
    def __init__(self, agent_id: int, x: float, y: float, floor: int, 
                 current_room: str, params: dict):
        """
        Initialize an agent
        
        Args:
            agent_id: Unique agent identifier
            x, y: Initial position
            floor: Initial floor
            current_room: Initial room ID
            params: Agent parameters from config
        """
        self.id = agent_id
        self.x = x
        self.y = y
        self.floor = floor
        self.current_room = current_room
        
        # Movement parameters
        self.speed_hall = params.get('speed_hall', 1.5)
        self.speed_stairs = params.get('speed_stairs', 0.8)
        self.speed_drag = params.get('speed_drag', 0.6)
        self.service_time_base = params.get('service_time_base', 5.0)
        
        # State machine
        self.state = AgentState.IDLE
        self.target_room: Optional[str] = None
        self.path: List[str] = []
        self.path_index = 0
        
        # Interpolated movement with waypoints (for doors)
        self.target_x: Optional[float] = None
        self.target_y: Optional[float] = None
        self.moving_to_room = False
        self.waypoints: List[Tuple[float, float]] = []  # Door waypoints
        self.current_waypoint = 0
        
        # Timing
        self.time_remaining_action = 0.0
        self.time_in_current_state = 0.0
        
        # Evacuee handling
        self.carrying_evacuee = False
        self.evacuee_source_room: Optional[str] = None
        
        # Statistics
        self.total_distance_traveled = 0.0
        self.rooms_cleared = 0
        self.evacuees_rescued = 0
        self.cumulative_hazard_exposure = 0.0
        
        # Safety status
        self.is_dead = False  # True if danger level > 0.95
        
        # History for visualization
        self.position_history: List[Tuple[float, float, int]] = [(x, y, floor)]
        self.max_history_length = 100
        
        # Communication (for latency modeling)
        self.last_comm_tick = 0
        self.knowledge_timestamp: dict = {}  # room_id -> tick last known
    
    def set_target(self, room_id: str, path: List[str]):
        """
        Set new target room and path
        
        Args:
            room_id: Target room ID
            path: List of room IDs forming path to target
        """
        self.target_room = room_id
        self.path = path if path else []
        self.path_index = 0
        
        if self.state == AgentState.IDLE:
            self.state = AgentState.MOVING
    
    def clear_target(self):
        """Clear current target and path"""
        self.target_room = None
        self.path = []
        self.path_index = 0
        self.state = AgentState.IDLE
    
    def update_position(self, x: float, y: float, floor: int, current_room: str):
        """Update agent position"""
        # Track distance traveled
        dx = x - self.x
        dy = y - self.y
        self.total_distance_traveled += (dx * dx + dy * dy) ** 0.5
        
        self.x = x
        self.y = y
        self.floor = floor
        self.current_room = current_room
        
        # Update history
        self.position_history.append((x, y, floor))
        if len(self.position_history) > self.max_history_length:
            self.position_history.pop(0)
    
    def move_towards(self, target_x: float, target_y: float, speed: float, dt: float) -> bool:
        """
        Move agent towards target position with given speed
        
        Args:
            target_x, target_y: Target position
            speed: Movement speed in m/s
            dt: Time delta in seconds
            
        Returns:
            True if target reached, False otherwise
        """
        dx = target_x - self.x
        dy = target_y - self.y
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance < 0.1:  # Close enough (10cm threshold)
            self.x = target_x
            self.y = target_y
            return True
        
        # Move towards target
        move_dist = min(speed * dt, distance)
        if distance > 0:
            self.x += (dx / distance) * move_dist
            self.y += (dy / distance) * move_dist
        
        self.total_distance_traveled += move_dist
        
        # Update history
        self.position_history.append((self.x, self.y, self.floor))
        if len(self.position_history) > self.max_history_length:
            self.position_history.pop(0)
        
        return False
    
    def start_searching(self, service_time: float):
        """Begin searching current room"""
        self.state = AgentState.SEARCHING
        self.time_remaining_action = service_time
        self.time_in_current_state = 0.0
    
    def start_rescuing(self, exit_room: str, path: List[str]):
        """
        Begin rescuing evacuee - set path to exit
        
        Args:
            exit_room: Exit room ID
            path: Path to exit
        """
        self.state = AgentState.DRAGGING
        self.carrying_evacuee = True
        self.target_room = exit_room
        self.path = path
        self.path_index = 0
    
    def complete_rescue(self):
        """Complete evacuee rescue at exit"""
        self.carrying_evacuee = False
        self.evacuee_source_room = None
        self.evacuees_rescued += 1
        self.state = AgentState.IDLE
        self.clear_target()
    
    def complete_search(self):
        """Complete searching current room"""
        self.rooms_cleared += 1
        self.state = AgentState.IDLE
    
    def advance_path(self) -> Optional[str]:
        """
        Advance to next room in path
        
        Returns:
            Next room ID, or None if path complete
        """
        if self.path_index < len(self.path):
            next_room = self.path[self.path_index]
            self.path_index += 1
            return next_room
        return None
    
    def get_current_speed(self, is_stair: bool = False) -> float:
        """Get current movement speed based on state"""
        if self.carrying_evacuee:
            return self.speed_drag
        elif is_stair:
            return self.speed_stairs
        else:
            return self.speed_hall
    
    def accumulate_hazard_exposure(self, hazard: float, dt: float):
        """Accumulate hazard exposure over time"""
        self.cumulative_hazard_exposure += hazard * dt
    
    def get_trail(self, length: int = 20) -> List[Tuple[float, float, int]]:
        """Get recent position trail for visualization"""
        if len(self.position_history) <= length:
            return self.position_history.copy()
        return self.position_history[-length:]
    
    def get_stats(self) -> dict:
        """Get agent statistics"""
        return {
            'agent_id': self.id,
            'state': self.state.value,
            'distance_traveled': self.total_distance_traveled,
            'rooms_cleared': self.rooms_cleared,
            'evacuees_rescued': self.evacuees_rescued,
            'hazard_exposure': self.cumulative_hazard_exposure
        }
    
    def __repr__(self):
        return (f"Agent({self.id}, state={self.state.value}, "
                f"room={self.current_room}, floor={self.floor}, "
                f"target={self.target_room})")

