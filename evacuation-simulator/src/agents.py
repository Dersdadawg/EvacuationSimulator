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
    """Evacuee trying to reach an exit"""
    
    # Danger level thresholds
    DANGER_SLOW_THRESHOLD = 0.3  # Start slowing down
    DANGER_FREEZE_THRESHOLD = 0.6  # Can't move without responder
    DANGER_UNCONSCIOUS_THRESHOLD = 0.9  # Become unconscious
    
    def __init__(self, x: int, y: int, speed: float = 1.0):
        super().__init__(x, y, speed)
        self.evacuated = False
        self.rescued = False
        self.stuck = False
        self.stuck_timer = 0
        self.path_history = [(x, y)]
        self.escorted_by = None  # Responder ID if being escorted
        self.unconscious = False  # Can't move at all, needs carrying
        
    def update(self, env: Environment, flow_field: FlowField) -> bool:
        """
        Move evacuee toward exit using flow field
        Responds to danger levels
        
        Returns:
            True if moved, False otherwise
        """
        if not self.active or self.evacuated or self.unconscious:
            return False
        
        # Check if at exit
        state = env.get_state(self.x, self.y)
        if state == CellState.EXIT:
            self.evacuated = True
            self.active = False
            return False
        
        # Check danger level at current position
        danger_level = env.get_danger_level(self.x, self.y)
        
        # Become unconscious if danger too high
        if danger_level >= self.DANGER_UNCONSCIOUS_THRESHOLD:
            self.unconscious = True
            self.stuck = True
            return False
        
        # Can't move if danger too high and not escorted
        if danger_level >= self.DANGER_FREEZE_THRESHOLD and self.escorted_by is None:
            self.stuck_timer += 1
            if self.stuck_timer > 10:
                self.stuck = True
            return False
        
        # Determine effective speed (reduced by danger level)
        effective_speed = self.speed
        
        # Slow down in moderate danger
        if danger_level >= self.DANGER_SLOW_THRESHOLD:
            danger_penalty = (danger_level - self.DANGER_SLOW_THRESHOLD) / (1.0 - self.DANGER_SLOW_THRESHOLD)
            effective_speed *= (1.0 - 0.5 * danger_penalty)  # Up to 50% slower
        
        # Even slower when escorted
        if self.escorted_by is not None:
            effective_speed *= 0.5
        
        # Accumulate movement
        self.movement_accumulator += effective_speed
        
        if self.movement_accumulator >= 1.0:
            self.movement_accumulator -= 1.0
            
            # Get next position from flow field
            next_pos = flow_field.get_best_direction(self.x, self.y)
            
            if next_pos:
                # Check if next position is too dangerous
                next_danger = env.get_danger_level(next_pos[0], next_pos[1])
                if next_danger >= self.DANGER_FREEZE_THRESHOLD and self.escorted_by is None:
                    # Too dangerous to enter
                    self.stuck_timer += 1
                    if self.stuck_timer > 10:
                        self.stuck = True
                    return False
                
                self.x, self.y = next_pos
                self.path_history.append((self.x, self.y))
                self.stuck_timer = 0
                return True
            else:
                self.stuck_timer += 1
                if self.stuck_timer > 10:
                    self.stuck = True
        
        return False
    
    def can_move(self, env: Environment) -> bool:
        """Check if evacuee can currently move"""
        if not self.active or self.evacuated or self.unconscious:
            return False
        
        # Can't move if danger too high and not escorted
        danger_level = env.get_danger_level(self.x, self.y)
        if danger_level >= self.DANGER_FREEZE_THRESHOLD and self.escorted_by is None:
            return False
        
        return True


class Responder(Agent):
    """Emergency responder sweeping building and rescuing evacuees"""
    
    # Danger level thresholds (responders are more resistant)
    DANGER_SLOW_THRESHOLD = 0.5  # Start slowing down
    DANGER_LIMIT_THRESHOLD = 0.95  # Can't enter even with equipment
    
    def __init__(self, x: int, y: int, speed: float = 1.0):
        super().__init__(x, y, speed)
        self.current_path = []
        self.current_task = None  # Target position for current sweep task
        self.rescued_count = 0
        self.distance_traveled = 0
        self.path_history = [(x, y)]
        self.escorting = None  # Evacuee being escorted
        
    def assign_task(self, target: Tuple[int, int], env: Environment):
        """
        Assign a sweep task (room to clear)
        
        Args:
            target: Target position to reach
            env: Environment
        """
        self.current_task = target
        self.current_path = AStar.find_path(env, self.get_position(), target, 
                                           can_cross_danger=True, hazard_penalty=2.0)
        
    def update(self, env: Environment, evacuees: List['Evacuee']) -> bool:
        """
        Update responder: move along path, rescue evacuees, clear rooms
        Responders can enter danger zones but are slowed
        
        Returns:
            True if moved, False otherwise
        """
        if not self.active:
            return False
        
        # Check for nearby evacuees to rescue
        self._check_for_rescues(evacuees, env)
        
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
                
                # Update escorted evacuee position
                if self.escorting:
                    self.escorting.x, self.escorting.y = self.x, self.y
                
                return True
        
        return False
    
    def _check_for_rescues(self, evacuees: List['Evacuee'], env: Environment):
        """Check for evacuees in danger nearby and rescue them"""
        for evacuee in evacuees:
            if evacuee.active and not evacuee.evacuated and not evacuee.rescued:
                # Check if evacuee is nearby (within 2 cells)
                dx = abs(evacuee.x - self.x)
                dy = abs(evacuee.y - self.y)
                
                if dx <= 2 and dy <= 2:
                    # Check if evacuee needs help
                    evac_danger = env.get_danger_level(evacuee.x, evacuee.y)
                    needs_rescue = (
                        evacuee.unconscious or
                        evacuee.stuck or
                        evac_danger >= Evacuee.DANGER_FREEZE_THRESHOLD
                    )
                    
                    if needs_rescue:
                        # Rescue evacuee
                        self._rescue_evacuee(evacuee)
    
    def _rescue_evacuee(self, evacuee: 'Evacuee'):
        """Start escorting an evacuee"""
        if self.escorting is None:  # Can only escort one at a time
            evacuee.rescued = True
            evacuee.escorted_by = self.id
            self.escorting = evacuee
            self.rescued_count += 1
    
    def has_reached_task(self) -> bool:
        """Check if responder has reached current task location"""
        if self.current_task is None:
            return True
        
        dx = abs(self.x - self.current_task[0])
        dy = abs(self.y - self.current_task[1])
        
        return dx <= 1 and dy <= 1
    
    def clear_task(self):
        """Clear current task"""
        self.current_task = None
        self.current_path = []
    
    def replan_path(self, env: Environment):
        """Replan path to current task (if hazards have changed)"""
        if self.current_task:
            new_path = AStar.find_path(env, self.get_position(), self.current_task,
                                      can_cross_danger=True, hazard_penalty=2.0)
            if new_path:
                self.current_path = new_path
    
    def release_evacuee(self):
        """Release escorted evacuee (when near exit)"""
        if self.escorting:
            self.escorting.escorted_by = None
            self.escorting = None


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
        """Count evacuees rescued by responders"""
        return sum(1 for e in self.evacuees if e.rescued)
    
    def count_active_evacuees(self) -> int:
        """Count evacuees still trying to evacuate"""
        return sum(1 for e in self.evacuees if e.active and not e.evacuated)
    
    def count_stuck(self) -> int:
        """Count stuck evacuees"""
        return sum(1 for e in self.evacuees if e.stuck)
    
    def get_total_responder_distance(self) -> int:
        """Get total distance traveled by all responders"""
        return sum(r.distance_traveled for r in self.responders)

