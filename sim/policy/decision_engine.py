"""Decision engine implementing weighted greedy TRP-inspired policy"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from ..env.environment import Environment
from ..agents.agent import Agent, AgentState


@dataclass
class RoomScore:
    """Score breakdown for a room"""
    room_id: str
    weight: float
    travel_time: float
    service_time: float
    score: float
    path: List[str]
    
    def __repr__(self):
        return (f"RoomScore({self.room_id}, w={self.weight:.2f}, "
                f"tt={self.travel_time:.1f}s, st={self.service_time:.1f}s, "
                f"score={self.score:.4f})")


class DecisionEngine:
    """Implements the weighted greedy sweep algorithm"""
    
    def __init__(self, environment: Environment, params: dict):
        """
        Initialize decision engine
        
        Args:
            environment: Building environment
            params: Policy parameters
        """
        self.env = environment
        self.params = params
        
        # Policy weights
        self.epsilon = params.get('epsilon', 0.001)
        self.lambda_param = params.get('lambda', 1.2)  # Paper: behavior parameter
        self.area_weight = params.get('area_weight', 1.0)
        self.evacuee_weight = params.get('evacuee_weight', 1.0)
        self.distance_weight = params.get('distance_weight', 1.0)
        
        # Agent parameters for time calculation
        self.agent_params = None
    
    def set_agent_params(self, agent_params: dict):
        """Set agent parameters for movement time calculations"""
        self.agent_params = agent_params
    
    def calculate_priority_index(self, room_id: str, agent_position: str) -> float:
        """
        Calculate room priority with GRANULAR values
        
        Formula: P_i(t) = A_i * E_i * (100 + λ*D_i) / (1 + distance/10)
        
        Args:
            room_id: Room to evaluate
            agent_position: Current agent position for accessibility check
            
        Returns:
            Priority index value (granular, not integers)
        """
        room = self.env.rooms[room_id]
        
        # E_i(t): Expected number of evacuees
        E_i = float(room.evacuees_remaining)
        
        # If no evacuees, priority = 0
        if E_i == 0:
            return 0.0
        
        # A_i(t): Accessibility (1 if accessible, 0 if not)
        path = self.env.get_shortest_path(agent_position, room_id)
        A_i = 1.0 if path is not None else 0.0
        
        if A_i == 0.0:
            return 0.0
        
        # Check if door is on fire (CRITICAL: can't enter if door is burning!)
        if hasattr(self.env, 'hazard_system') and self.env.hazard_system:
            # Get actual door position from layout connections
            door_pos = None
            if hasattr(self.env, 'layout') and 'connections' in self.env.layout:
                for conn in self.env.layout['connections']:
                    if conn['from'] == room_id and 'door_pos' in conn:
                        door_pos = (conn['door_pos']['x'], conn['door_pos']['y'])
                        break
            
            if door_pos:
                # Check if door cells are burning (2m door = 4 cells wide)
                # Also check cells on both sides (in room and in hallway)
                for dx in [-1.0, -0.5, 0.0, 0.5, 1.0]:  # Check 5 cells (2.5m) around door
                    for dy in [-0.5, 0.0, 0.5]:  # Check in front, at, and behind door
                        door_x = door_pos[0] + dx * 0.5
                        door_y = door_pos[1] + dy * 0.5
                        door_cell_key = (round(door_x / 0.5) * 0.5 + 0.25, round(door_y / 0.5) * 0.5 + 0.25)
                        if door_cell_key in self.env.hazard_system.cells:
                            door_cell = self.env.hazard_system.cells[door_cell_key]
                            if door_cell.is_burning or door_cell.danger_level > 0.85:
                                return 0.0  # Door blocked by fire!
        
        # D_i(t): Average danger level [0, 1]
        D_i = room.hazard
        
        # Calculate distance from agent to room
        if agent_position in self.env.rooms:
            agent_room = self.env.rooms[agent_position]
            distance = abs(room.x - agent_room.x) + abs(room.y - agent_room.y)
        else:
            distance = 0.0
        
        # Use minimum distance of 5m to prevent priority spikes when agent in room
        distance = max(distance, 5.0)
        
        # λ: Danger multiplier
        lambda_val = 10.0  # Danger weight
        
        # SIMPLE GRANULAR FORMULA: P = E × (10 + λ×D) / (dist/10)
        # Keeps priorities in reasonable range (not 100s!)
        # E=2, D=0.00, dist=10: P = 2×10 / 1.0 = 20.00
        # E=2, D=0.20, dist=10: P = 2×12 / 1.0 = 24.00 ← Fire room slightly higher
        # E=5, D=0.20, dist=10: P = 5×12 / 1.0 = 60.00 ← More people = higher!
        numerator = E_i * (10.0 + lambda_val * D_i)
        denominator = distance / 10.0
        priority = A_i * numerator / denominator
        
        return priority
    
    def calculate_room_weight(self, room_id: str, distance: float) -> float:
        """
        Calculate room weight: w_i = (A_i × E_i) / (D_i + ε)
        
        Args:
            room_id: Room to evaluate
            distance: Distance to room
        
        Returns:
            Room weight value
        """
        room = self.env.rooms[room_id]
        
        # Area component (normalized by typical room size)
        A_i = room.area * self.area_weight
        
        # Evacuee component (expected count)
        # For MVP, use actual count; in real scenario might use probability
        E_i = (room.evacuee_count + 1) * self.evacuee_weight
        
        # Distance component (penalize far rooms)
        D_i = distance * self.distance_weight
        
        # Weight formula
        weight = (A_i * E_i) / (D_i + self.epsilon)
        
        # Apply hazard penalty (reduce weight for high-hazard rooms)
        hazard_penalty = 1.0 - (room.hazard * 0.5)  # Up to 50% reduction
        weight *= max(0.1, hazard_penalty)
        
        return weight
    
    def estimate_travel_time(self, agent: Agent, path: List[str]) -> float:
        """
        Estimate time to traverse a path
        
        Args:
            agent: Agent that would traverse path
            path: List of room IDs
        
        Returns:
            Estimated time in seconds
        """
        if not path or len(path) < 2:
            return 0.0
        
        total_time = 0.0
        
        for i in range(len(path) - 1):
            from_id = path[i]
            to_id = path[i + 1]
            
            # Get edge data
            if self.env.graph.has_edge(from_id, to_id):
                edge = self.env.graph[from_id][to_id]
                distance = edge.get('distance', 10.0)
                is_stair = edge.get('is_stair', False)
            else:
                # Fallback: use room-to-room distance
                distance = self.env.rooms[from_id].distance_to(self.env.rooms[to_id])
                is_stair = False
            
            # Calculate time based on speed
            speed = agent.get_current_speed(is_stair)
            total_time += distance / speed
        
        return total_time
    
    def estimate_service_time(self, room_id: str) -> float:
        """
        Estimate time to search a room
        
        Args:
            room_id: Room to search
        
        Returns:
            Estimated service time in seconds
        """
        room = self.env.rooms[room_id]
        
        if self.agent_params:
            base_time = self.agent_params.get('service_time_base', 5.0)
        else:
            base_time = 5.0
        
        # Scale by room area (larger rooms take longer)
        area_factor = 1.0 + (room.area / 100.0) * 0.5  # +50% time per 100 sq units
        
        # Scale by hazard (higher hazard = slower search)
        hazard_factor = 1.0 + room.hazard * 0.5  # Up to +50% time at max hazard
        
        return base_time * area_factor * hazard_factor
    
    def score_room(self, agent: Agent, room_id: str) -> Optional[RoomScore]:
        """
        Calculate score for a room from agent's perspective
        
        Args:
            agent: Agent evaluating the room
            room_id: Room to score
        
        Returns:
            RoomScore object or None if room not reachable
        """
        room = self.env.rooms[room_id]
        
        # Skip if already cleared
        if room.cleared:
            return None
        
        # Skip exits and stairs (not searchable)
        if room.is_exit or room.is_stair:
            return None
        
        # Get path from agent's current room to target
        path = self.env.get_shortest_path(agent.current_room, room_id)
        if not path:
            return None
        
        # Calculate distance
        distance = self.env.get_path_length(agent.current_room, room_id)
        
        # Calculate components
        weight = self.calculate_room_weight(room_id, distance)
        travel_time = self.estimate_travel_time(agent, path)
        service_time = self.estimate_service_time(room_id)
        
        # Final score: score_i = w_i / (travel_time + service_time)
        total_time = travel_time + service_time
        if total_time < 0.1:
            total_time = 0.1  # Avoid division by zero
        
        score = weight / total_time
        
        return RoomScore(
            room_id=room_id,
            weight=weight,
            travel_time=travel_time,
            service_time=service_time,
            score=score,
            path=path
        )
    
    def select_next_room(self, agent: Agent) -> Optional[RoomScore]:
        """
        Select best next room for agent using greedy policy
        
        Args:
            agent: Agent to select room for
        
        Returns:
            RoomScore for best room, or None if no rooms available
        """
        # Get all uncleared rooms
        uncleared = self.env.get_uncleared_rooms()
        
        if not uncleared:
            return None
        
        # Score all rooms
        scores: List[RoomScore] = []
        for room_id in uncleared:
            room_score = self.score_room(agent, room_id)
            if room_score:
                scores.append(room_score)
        
        if not scores:
            return None
        
        # Select room with highest score (greedy)
        best_score = max(scores, key=lambda s: s.score)
        
        return best_score
    
    def select_rooms_for_all_agents(self, agents: List[Agent]) -> dict:
        """
        Select best rooms for multiple agents (coordination)
        
        Args:
            agents: List of idle agents needing assignments
        
        Returns:
            Dictionary mapping agent_id -> RoomScore
        """
        assignments = {}
        assigned_rooms = set()
        
        # Sort agents by some priority (e.g., by ID for consistency)
        sorted_agents = sorted(agents, key=lambda a: a.id)
        
        for agent in sorted_agents:
            # Get all uncleared rooms not yet assigned
            uncleared = [rid for rid in self.env.get_uncleared_rooms() 
                        if rid not in assigned_rooms]
            
            if not uncleared:
                break
            
            # Score available rooms
            scores: List[RoomScore] = []
            for room_id in uncleared:
                room_score = self.score_room(agent, room_id)
                if room_score:
                    scores.append(room_score)
            
            if scores:
                best_score = max(scores, key=lambda s: s.score)
                assignments[agent.id] = best_score
                assigned_rooms.add(best_score.room_id)
        
        return assignments
    
    def get_path_to_exit(self, from_room_id: str) -> Tuple[Optional[str], Optional[List[str]]]:
        """
        Get path to nearest exit
        
        Args:
            from_room_id: Starting room
        
        Returns:
            Tuple of (exit_room_id, path) or (None, None) if no path
        """
        nearest_exit = self.env.get_nearest_exit(from_room_id)
        if not nearest_exit:
            return None, None
        
        path = self.env.get_shortest_path(from_room_id, nearest_exit)
        return nearest_exit, path

