"""
Agents module: Responder and Evacuee classes with movement logic
"""

from typing import Tuple, Optional, List
from src.environment import Environment, CellState
from src.pathfinding import AStar, FlowField


class Agent:
    """Base class for all agents"""
    
    _id_counter = 0
    
    def __init__(self, x: int, y: int, speed: float = 1.0):
        self.id = Agent._id_counter
        Agent._id_counter += 1
        self.x = x
        self.y = y
        self.speed = speed
        self.active = True
        self.movement_accumulator = 0.0  # For fractional movement
        
    def get_position(self) -> Tuple[int, int]:
        return (self.x, self.y)
    
    def set_position(self, x: int, y: int):
        self.x = x
        self.y = y


class Evacuee(Agent):
    """
    Evacuee - STATIC in this model
    Evacuees don't move; they wait in rooms to be found/rescued by responders
    """
    
    # Danger level thresholds
    DANGER_UNCONSCIOUS_THRESHOLD = 0.9  # Become unconscious from exposure
    
    def __init__(self, x: int, y: int, speed: float = 1.0):
        super().__init__(x, y, speed)
        self.evacuated = False
        self.rescued = False  # Found by responder
        self.unconscious = False  # High danger exposure
        self.room_id = None  # Which room they're in
        self.found = False  # Discovered by responder
        self.danger_exposure_time = 0  # Time spent in high danger
        
    def update(self, env: Environment, flow_field: FlowField = None) -> bool:
        """
        Evacuees are STATIC - they don't move
        They only track danger exposure and may become unconscious
        
        Returns:
            False (evacuees don't move)
        """
        if not self.active or self.evacuated or self.found:
            return False
        
        # Check danger level at current position
        danger_level = env.get_danger_level(self.x, self.y)
        
        # Track danger exposure
        if danger_level >= 0.6:
            self.danger_exposure_time += 1
        
        # Become unconscious if exposed to high danger too long
        if danger_level >= self.DANGER_UNCONSCIOUS_THRESHOLD:
            self.danger_exposure_time += 2  # High danger counts double
        
        if self.danger_exposure_time > 20:  # 20 timesteps in danger
            self.unconscious = True
        
        return False  # Evacuees are static
    
    def can_move(self, env: Environment) -> bool:
        """Evacuees are static - always returns False"""
        return False


class Responder(Agent):
    """
    Emergency responder using Traveling Repairman Problem optimization
    Visits rooms based on priority weights calculated from:
    - Expected occupancy
    - Danger level
    - Time to untenability
    - Information/reports
    - Accessibility
    - Travel time
    """
    
    # Danger level thresholds (responders are more resistant)
    DANGER_SLOW_THRESHOLD = 0.5  # Start slowing down
    DANGER_LIMIT_THRESHOLD = 0.95  # Can't enter even with equipment
    
    def __init__(self, x: int, y: int, speed: float = 1.0):
        super().__init__(x, y, speed)
        self.current_path = []
        self.current_room_target = None  # Current room being cleared
        self.rescued_count = 0
        self.distance_traveled = 0
        self.path_history = [(x, y)]
        self.rooms_cleared = set()  # Set of cleared room IDs
        self.evacuees_found = []  # List of evacuee IDs found
        self.escorting = None  # Evacuee currently being escorted
        self.escort_target_exit = None  # Exit to escort to
        self.room_search_time = 0  # Time spent searching current room
        
    def assign_room_task(self, room_info, env: Environment):
        """
        Assign a room to clear (TRP optimization)
        
        Args:
            room_info: RoomInfo object with priority weight
            env: Environment
        """
        self.current_room_target = room_info
        self.room_search_time = 0  # Reset search time for new room
        self.current_path = AStar.find_path(
            env, 
            self.get_position(), 
            room_info.center,
            can_cross_danger=True, 
            hazard_penalty=2.0
        )
        
    def update(self, env: Environment, evacuees: List['Evacuee']) -> bool:
        """
        Update responder: move along path, rescue evacuees, clear rooms
        Responders can enter danger zones but are slowed
        
        Returns:
            True if moved, False otherwise
        """
        if not self.active:
            return False
        
        # Check for evacuees in current room
        self._check_for_evacuees_in_room(evacuees, env)
        
        # Move along current path
        if self.current_path and len(self.current_path) > 1:
            # Check danger level at current position
            danger_level = env.get_danger_level(self.x, self.y)
            
            # Responders slow down in high danger
            effective_speed = self.speed
            if danger_level >= self.DANGER_SLOW_THRESHOLD:
                danger_penalty = min(1.0, (danger_level - self.DANGER_SLOW_THRESHOLD) / (self.DANGER_LIMIT_THRESHOLD - self.DANGER_SLOW_THRESHOLD))
                effective_speed *= (1.0 - 0.4 * danger_penalty)  # Up to 40% slower
            
            # Accumulate movement
            self.movement_accumulator += effective_speed
            
            if self.movement_accumulator >= 1.0:
                self.movement_accumulator -= 1.0
                
                # Check if next position is too dangerous
                next_pos = self.current_path[1]
                next_danger = env.get_danger_level(next_pos[0], next_pos[1])
                
                if next_danger >= self.DANGER_LIMIT_THRESHOLD:
                    # Too dangerous even for responder, need to replan
                    return False
                
                # Move to next waypoint
                self.x, self.y = next_pos
                self.current_path.pop(0)
                self.path_history.append((self.x, self.y))
                self.distance_traveled += 1
                
                # Move escorted evacuee with responder
                if self.escorting:
                    self.escorting.x, self.escorting.y = self.x, self.y
                    
                    # Check if reached exit
                    if env.get_state(self.x, self.y) == CellState.EXIT:
                        # Evacuee is safe!
                        self.escorting.evacuated = True
                        self.escorting.active = False
                        self.escorting = None
                        self.escort_target_exit = None
                        # Will return to room clearing on next update
                
                return True
        
        return False
    
    def _check_for_evacuees_in_room(self, evacuees: List['Evacuee'], env: Environment):
        """
        Find evacuees in current room and start escorting to nearest exit
        """
        # Don't look for more evacuees if already escorting
        if self.escorting is not None:
            return
            
        if self.current_room_target is None:
            return
        
        # Check if responder is in target room
        current_cell = env.get_cell(self.x, self.y)
        if current_cell and current_cell.room_id == self.current_room_target.room_id:
            # In the room, find evacuees here
            for evacuee in evacuees:
                if evacuee.active and not evacuee.found:
                    evac_cell = env.get_cell(evacuee.x, evacuee.y)
                    if evac_cell and evac_cell.room_id == self.current_room_target.room_id:
                        # Found evacuee! Start escorting to exit
                        evacuee.found = True
                        evacuee.rescued = True
                        self.evacuees_found.append(evacuee.id)
                        self.rescued_count += 1
                        self._start_escort(evacuee, env)
                        break  # Escort one at a time
    
    def _start_escort(self, evacuee: 'Evacuee', env: Environment):
        """Start escorting evacuee to nearest exit"""
        self.escorting = evacuee
        
        # Find nearest exit using A* (considering danger)
        nearest_exit = None
        shortest_path = None
        min_cost = float('inf')
        
        for exit_pos in env.exits:
            path = AStar.find_path(
                env,
                self.get_position(),
                exit_pos,
                can_cross_danger=True,
                hazard_penalty=3.0  # Higher penalty when escorting
            )
            if path and len(path) < min_cost:
                min_cost = len(path)
                shortest_path = path
                nearest_exit = exit_pos
        
        if nearest_exit:
            self.escort_target_exit = nearest_exit
            self.current_path = shortest_path
            # Clear room target while escorting
            self.current_room_target = None
    
    def has_reached_room(self, env: Environment) -> bool:
        """Check if responder has reached and is inside current room"""
        if self.current_room_target is None:
            return False  # No room assigned, so not reached
        
        current_cell = env.get_cell(self.x, self.y)
        if current_cell and current_cell.room_id == self.current_room_target.room_id:
            # In the room, increment search time
            self.room_search_time += 1
            return True
        
        return False
    
    def has_searched_room_enough(self) -> bool:
        """Check if responder has searched room long enough"""
        # Need to search for at least 3 timesteps to find evacuees
        return self.room_search_time >= 3
    
    def clear_room(self):
        """Mark current room as cleared"""
        if self.current_room_target:
            self.rooms_cleared.add(self.current_room_target.room_id)
            self.current_room_target = None
        self.current_path = []
    
    def replan_path(self, env: Environment):
        """Replan path to current room (if hazards have changed)"""
        if self.current_room_target:
            new_path = AStar.find_path(
                env, 
                self.get_position(), 
                self.current_room_target.center,
                can_cross_danger=True, 
                hazard_penalty=2.0
            )
            if new_path:
                self.current_path = new_path


class AgentManager:
    """Manages all agents in the simulation"""
    
    def __init__(self):
        self.evacuees: List[Evacuee] = []
        self.responders: List[Responder] = []
        
    def add_evacuee(self, x: int, y: int, speed: float = 1.0) -> Evacuee:
        """Add an evacuee"""
        evacuee = Evacuee(x, y, speed)
        self.evacuees.append(evacuee)
        return evacuee
    
    def add_responder(self, x: int, y: int, speed: float = 1.0) -> Responder:
        """Add a responder"""
        responder = Responder(x, y, speed)
        self.responders.append(responder)
        return responder
    
    def get_evacuee_positions(self) -> List[Tuple[int, int]]:
        """Get positions of all active evacuees"""
        return [e.get_position() for e in self.evacuees if e.active and not e.evacuated]
    
    def get_responder_positions(self) -> List[Tuple[int, int]]:
        """Get positions of all active responders"""
        return [r.get_position() for r in self.responders if r.active]
    
    def count_evacuated(self) -> int:
        """Count evacuees who reached exits"""
        return sum(1 for e in self.evacuees if e.evacuated)
    
    def count_rescued(self) -> int:
        """Count evacuees found/rescued by responders"""
        return sum(1 for e in self.evacuees if e.found or e.rescued)
    
    def count_active_evacuees(self) -> int:
        """Count evacuees not yet found (static model)"""
        return sum(1 for e in self.evacuees if e.active and not e.found)
    
    def count_unconscious(self) -> int:
        """Count evacuees who became unconscious"""
        return sum(1 for e in self.evacuees if e.unconscious)
    
    def get_total_responder_distance(self) -> int:
        """Get total distance traveled by all responders"""
        return sum(r.distance_traveled for r in self.responders)

