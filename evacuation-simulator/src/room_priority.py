"""
Room Priority System: Calculate room weights for Traveling Repairman Problem
Responders optimize routes to visit rooms based on:
- Expected occupancy
- Danger level
- Time to untenability
- Information/reports
- Accessibility
- Travel time
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from src.environment import Environment, Cell


@dataclass
class RoomInfo:
    """Information about a room for priority calculation"""
    room_id: int
    center: Tuple[int, int]  # Room center coordinates
    cells: List[Tuple[int, int]]  # All cells in this room
    expected_occupancy: float = 1.0  # Expected number of people
    reported_occupancy: Optional[int] = None  # Actual reports
    is_accessible: bool = True  # Can responders enter?
    is_cleared: bool = False  # Has been verified clear
    
    # Time-varying
    avg_danger: float = 0.0  # Current average danger level
    time_to_untenability: float = float('inf')  # Timesteps until uninhabitable
    
    def __hash__(self):
        return hash(self.room_id)


class RoomWeightCalculator:
    """
    Calculates priority weights for rooms using Traveling Repairman Problem logic
    
    Weight = Urgency / Cost
    where:
    - Urgency = f(occupancy, danger, time_to_untenability, information)
    - Cost = travel_time
    
    Higher weight = higher priority
    """
    
    def __init__(self, env: Environment):
        self.env = env
        self.rooms: Dict[int, RoomInfo] = {}
        self._identify_rooms()
        
        # Weight parameters (tunable)
        self.w_occupancy = 1.0  # Weight for expected occupancy
        self.w_danger = 0.8  # Weight for danger level
        self.w_time = 1.2  # Weight for time urgency
        self.w_info = 0.5  # Weight for information gain
        self.w_access_penalty = 100.0  # Penalty if inaccessible
        
    def _identify_rooms(self):
        """Identify all rooms in the environment"""
        room_cells = {}
        
        # Collect cells by room_id
        for y in range(self.env.height):
            for x in range(self.env.width):
                cell = self.env.get_cell(x, y)
                if cell and cell.room_id is not None:
                    if cell.room_id not in room_cells:
                        room_cells[cell.room_id] = []
                    room_cells[cell.room_id].append((x, y))
        
        # Create RoomInfo objects
        for room_id, cells in room_cells.items():
            # Calculate center
            cx = sum(x for x, y in cells) // len(cells)
            cy = sum(y for x, y in cells) // len(cells)
            
            # Estimate expected occupancy based on room size
            # Larger rooms = more people (simple heuristic)
            expected_occupancy = max(1.0, len(cells) / 50.0)
            
            room_info = RoomInfo(
                room_id=room_id,
                center=(cx, cy),
                cells=cells,
                expected_occupancy=expected_occupancy
            )
            
            self.rooms[room_id] = room_info
    
    def update_room_states(self, env: Environment, timestep: int):
        """Update dynamic room properties (danger, time to untenability)"""
        for room_id, room in self.rooms.items():
            # a) Calculate average danger level
            danger_sum = 0.0
            max_danger = 0.0
            
            for x, y in room.cells:
                danger = env.get_danger_level(x, y)
                danger_sum += danger
                max_danger = max(max_danger, danger)
            
            room.avg_danger = danger_sum / len(room.cells)
            
            # b) Estimate time to untenability
            # If danger is spreading, estimate when room becomes uninhabitable
            if room.avg_danger < 0.3:
                # Safe, look at adjacent rooms for threats
                adjacent_danger = self._get_adjacent_danger(room, env)
                if adjacent_danger > 0.5:
                    # Danger nearby, estimate spread time
                    # Simple model: higher adjacent danger = faster spread
                    room.time_to_untenability = 20.0 / (adjacent_danger + 0.1)
                else:
                    room.time_to_untenability = float('inf')  # Safe for now
            elif room.avg_danger < 0.6:
                # Moderate danger, becoming critical soon
                danger_rate = 0.05  # Assume danger increases ~0.05 per timestep
                room.time_to_untenability = (0.9 - room.avg_danger) / danger_rate
            else:
                # High danger, already critical
                room.time_to_untenability = 5.0  # Very urgent
            
            # c) Check accessibility (blocked by walls/danger)
            room.is_accessible = self._check_accessibility(room, env)
    
    def _get_adjacent_danger(self, room: RoomInfo, env: Environment) -> float:
        """Get average danger level of adjacent cells outside room"""
        adjacent_danger = []
        
        for x, y in room.cells:
            for nx, ny in env.get_neighbors_8(x, y, can_cross_danger=True):
                if (nx, ny) not in room.cells:
                    danger = env.get_danger_level(nx, ny)
                    adjacent_danger.append(danger)
        
        return np.mean(adjacent_danger) if adjacent_danger else 0.0
    
    def _check_accessibility(self, room: RoomInfo, env: Environment) -> bool:
        """Check if room is accessible (not completely surrounded by high danger)"""
        # Room is accessible if there's at least one entry point with danger < 0.8
        entry_points = []
        
        for x, y in room.cells:
            for nx, ny in env.get_neighbors(x, y):
                cell = env.get_cell(nx, ny)
                if cell and cell.room_id != room.room_id:
                    danger = env.get_danger_level(nx, ny)
                    if danger < 0.8:  # Responders can traverse
                        return True
        
        return False
    
    def add_report(self, room_id: int, occupancy: int):
        """
        Add information report about a room (e.g., "3 people reported in room 5")
        This increases urgency via Bayesian update
        """
        if room_id in self.rooms:
            room = self.rooms[room_id]
            room.reported_occupancy = occupancy
            # Update expected value with report
            if occupancy > 0:
                room.expected_occupancy = max(room.expected_occupancy, float(occupancy))
    
    def calculate_urgency(self, room: RoomInfo, current_time: int) -> float:
        """
        Calculate urgency score for a room
        
        Urgency = occupancy * danger_factor * time_factor * info_factor
        """
        if room.is_cleared:
            return 0.0  # Already cleared
        
        # Factor a) Expected occupancy (more people = higher urgency)
        occupancy_score = room.expected_occupancy
        
        # Factor d) Information bonus (confirmed reports increase urgency)
        info_factor = 1.0
        if room.reported_occupancy is not None and room.reported_occupancy > 0:
            info_factor = 1.5  # 50% boost for confirmed occupancy
            occupancy_score = max(occupancy_score, room.reported_occupancy)
        
        # Factor b) Danger level (higher danger = more urgent)
        # Normalize to [0, 1] where 1 is most urgent
        if room.avg_danger < 0.3:
            danger_factor = 0.5  # Low priority if safe
        elif room.avg_danger < 0.6:
            danger_factor = 1.0  # Medium priority
        else:
            danger_factor = 1.5  # High priority if dangerous
        
        # Factor c) Time to untenability (less time = more urgent)
        # Use exponential decay: urgency increases as time decreases
        if room.time_to_untenability == float('inf'):
            time_factor = 0.5  # Not urgent if no immediate threat
        else:
            # Urgency increases exponentially as deadline approaches
            time_factor = np.exp(-room.time_to_untenability / 30.0) + 0.5
        
        # Factor e) Accessibility (inaccessible rooms have infinite cost, handled separately)
        
        # Combine factors
        urgency = (
            self.w_occupancy * occupancy_score * 
            self.w_danger * danger_factor * 
            self.w_time * time_factor * 
            self.w_info * info_factor
        )
        
        return urgency
    
    def calculate_weight(self, room: RoomInfo, responder_pos: Tuple[int, int], 
                        travel_time: float, current_time: int) -> float:
        """
        Calculate priority weight for Traveling Repairman Problem
        
        Weight = Urgency / Cost
        
        Args:
            room: Room to evaluate
            responder_pos: Current responder position
            travel_time: Estimated time to reach room (factor f)
            current_time: Current simulation timestep
        
        Returns:
            Priority weight (higher = visit sooner)
        """
        if room.is_cleared:
            return 0.0
        
        # Factor e) Accessibility
        if not room.is_accessible:
            return 0.0  # Infinite cost
        
        # Calculate urgency
        urgency = self.calculate_urgency(room, current_time)
        
        # Factor f) Travel time (cost)
        # Add small constant to avoid division by zero
        cost = travel_time + 1.0
        
        # Weight = Urgency / Cost (benefit per unit time)
        weight = urgency / cost
        
        return weight
    
    def get_next_room_priority(self, responder_pos: Tuple[int, int], 
                               current_time: int,
                               path_finder) -> Optional[RoomInfo]:
        """
        Get next room to visit using TRP logic
        
        Args:
            responder_pos: Current responder position
            current_time: Current timestep
            path_finder: AStar pathfinder to calculate travel times
        
        Returns:
            Highest priority room to visit next
        """
        best_room = None
        best_weight = 0.0
        
        from src.pathfinding import AStar
        
        for room in self.rooms.values():
            if room.is_cleared or not room.is_accessible:
                continue
            
            # Calculate travel time to room
            path = AStar.find_path(
                self.env, 
                responder_pos, 
                room.center,
                can_cross_danger=True,
                hazard_penalty=2.0
            )
            
            if path:
                travel_time = len(path)
            else:
                continue  # Can't reach
            
            # Calculate weight
            weight = self.calculate_weight(room, responder_pos, travel_time, current_time)
            
            if weight > best_weight:
                best_weight = weight
                best_room = room
        
        return best_room
    
    def mark_room_cleared(self, room_id: int):
        """Mark a room as cleared/verified"""
        if room_id in self.rooms:
            self.rooms[room_id].is_cleared = True
    
    def get_all_rooms(self) -> List[RoomInfo]:
        """Get list of all rooms"""
        return list(self.rooms.values())
    
    def get_uncleared_rooms(self) -> List[RoomInfo]:
        """Get list of uncleared rooms"""
        return [r for r in self.rooms.values() if not r.is_cleared]
    
    def get_room_by_position(self, x: int, y: int) -> Optional[RoomInfo]:
        """Get room containing given position"""
        cell = self.env.get_cell(x, y)
        if cell and cell.room_id is not None:
            return self.rooms.get(cell.room_id)
        return None

