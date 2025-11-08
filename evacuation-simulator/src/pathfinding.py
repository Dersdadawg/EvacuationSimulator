"""
Pathfinding module: A* for responders and flow-field for evacuees
"""

import heapq
import numpy as np
from typing import List, Tuple, Optional, Dict, Set
from src.environment import Environment, CellState


class AStar:
    """A* pathfinding algorithm for responders"""
    
    @staticmethod
    def heuristic(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Manhattan distance heuristic"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    @staticmethod
    def find_path(env: Environment, start: Tuple[int, int], goal: Tuple[int, int],
                  can_cross_danger: bool = True, hazard_penalty: float = 5.0) -> Optional[List[Tuple[int, int]]]:
        """
        Find path from start to goal using A*
        
        Args:
            env: Environment
            start: Starting position (x, y)
            goal: Goal position (x, y)
            can_cross_danger: Whether agent can traverse dangerous cells
            hazard_penalty: Additional cost for crossing dangerous cells
        
        Returns:
            List of (x, y) positions from start to goal, or None if no path exists
        """
        if not env.is_walkable(goal[0], goal[1], can_cross_danger):
            return None
        
        # Priority queue: (f_score, counter, position, path)
        counter = 0
        heap = [(0, counter, start, [start])]
        visited = {start: 0}  # position -> g_score
        
        while heap:
            f_score, _, current, path = heapq.heappop(heap)
            
            if current == goal:
                return path
            
            current_g = visited[current]
            
            # Explore neighbors
            for neighbor in env.get_neighbors(current[0], current[1], can_cross_danger):
                # Calculate cost
                move_cost = 1.0
                
                # Add penalty for dangerous cells
                state = env.get_state(neighbor[0], neighbor[1])
                if state == CellState.DANGER:
                    move_cost += hazard_penalty
                
                new_g = current_g + move_cost
                
                # If we found a better path to this neighbor
                if neighbor not in visited or new_g < visited[neighbor]:
                    visited[neighbor] = new_g
                    h = AStar.heuristic(neighbor, goal)
                    new_f = new_g + h
                    
                    counter += 1
                    new_path = path + [neighbor]
                    heapq.heappush(heap, (new_f, counter, neighbor, new_path))
        
        return None  # No path found
    
    @staticmethod
    def find_nearest_target(env: Environment, start: Tuple[int, int], 
                           targets: List[Tuple[int, int]], 
                           can_cross_danger: bool = True) -> Optional[Tuple[int, int]]:
        """
        Find nearest reachable target from start position
        
        Returns:
            Nearest target position or None
        """
        nearest = None
        min_distance = float('inf')
        
        for target in targets:
            path = AStar.find_path(env, start, target, can_cross_danger)
            if path and len(path) < min_distance:
                min_distance = len(path)
                nearest = target
        
        return nearest


class FlowField:
    """Flow field pathfinding for evacuees (multi-source Dijkstra)"""
    
    def __init__(self, env: Environment):
        self.env = env
        self.distance_field = None
        self.direction_field = None
        
    def compute(self, goals: List[Tuple[int, int]], avoid_danger: bool = True,
                density_penalty: float = 0.5):
        """
        Compute flow field from multiple goal positions (exits)
        
        Args:
            goals: List of goal positions (exits)
            avoid_danger: Whether to avoid dangerous cells
            density_penalty: Penalty for cells with high evacuee density
        """
        width, height = self.env.width, self.env.height
        
        # Initialize distance field with infinity
        self.distance_field = np.full((height, width), np.inf)
        self.direction_field = np.zeros((height, width, 2))  # (dx, dy) for each cell
        
        # Multi-source Dijkstra: start from all goals
        heap = []
        for goal in goals:
            if self.env.is_walkable(goal[0], goal[1], can_cross_danger=not avoid_danger):
                self.distance_field[goal[1], goal[0]] = 0
                heapq.heappush(heap, (0, goal))
        
        visited = set()
        
        while heap:
            dist, (x, y) = heapq.heappop(heap)
            
            if (x, y) in visited:
                continue
            visited.add((x, y))
            
            # Explore neighbors
            for nx, ny in self.env.get_neighbors(x, y, can_cross_danger=not avoid_danger):
                if (nx, ny) in visited:
                    continue
                
                # Calculate cost
                move_cost = 1.0
                
                # Add penalty for dangerous cells
                if avoid_danger:
                    state = self.env.get_state(nx, ny)
                    if state == CellState.DANGER:
                        move_cost += 10.0  # High penalty to avoid danger
                
                new_dist = dist + move_cost
                
                if new_dist < self.distance_field[ny, nx]:
                    self.distance_field[ny, nx] = new_dist
                    # Direction points from (nx, ny) toward (x, y)
                    self.direction_field[ny, nx] = [x - nx, y - ny]
                    heapq.heappush(heap, (new_dist, (nx, ny)))
    
    def get_best_direction(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """
        Get best neighbor to move to from current position
        
        Returns:
            Next position (x, y) or None if at goal/no path
        """
        if self.distance_field is None:
            return None
        
        current_dist = self.distance_field[y, x]
        
        if current_dist == 0 or current_dist == np.inf:
            return None  # At goal or unreachable
        
        # Find neighbor with lowest distance (gradient descent)
        best_neighbor = None
        best_dist = current_dist
        
        for nx, ny in self.env.get_neighbors(x, y, can_cross_danger=False):
            neighbor_dist = self.distance_field[ny, nx]
            if neighbor_dist < best_dist:
                best_dist = neighbor_dist
                best_neighbor = (nx, ny)
        
        return best_neighbor
    
    def get_distance(self, x: int, y: int) -> float:
        """Get distance value at position"""
        if self.distance_field is None:
            return np.inf
        if 0 <= x < self.env.width and 0 <= y < self.env.height:
            return self.distance_field[y, x]
        return np.inf
    
    def is_reachable(self, x: int, y: int) -> bool:
        """Check if position has path to any goal"""
        return self.get_distance(x, y) < np.inf


class RoomSweepPlanner:
    """Plans room sweep tasks for responders"""
    
    def __init__(self, env: Environment):
        self.env = env
        self.uncleared_rooms = self._identify_rooms()
        
    def _identify_rooms(self) -> List[Tuple[int, int]]:
        """Identify all room center points that need clearing"""
        rooms = {}
        
        for y in range(self.env.height):
            for x in range(self.env.width):
                cell = self.env.get_cell(x, y)
                if cell and cell.room_id is not None:
                    if cell.room_id not in rooms:
                        rooms[cell.room_id] = []
                    rooms[cell.room_id].append((x, y))
        
        # Get center of each room
        room_centers = []
        for room_id, cells in rooms.items():
            if cells:
                cx = sum(x for x, y in cells) // len(cells)
                cy = sum(y for x, y in cells) // len(cells)
                room_centers.append((cx, cy))
        
        return room_centers
    
    def assign_task(self, responder_pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """
        Assign nearest uncleared room to responder
        
        Returns:
            Target room center or None if all cleared
        """
        if not self.uncleared_rooms:
            return None
        
        # Find nearest uncleared room
        nearest = AStar.find_nearest_target(self.env, responder_pos, 
                                           self.uncleared_rooms, can_cross_danger=True)
        
        return nearest
    
    def mark_room_cleared(self, position: Tuple[int, int], radius: int = 5):
        """Mark room at position as cleared"""
        # Remove any uncleared rooms within radius
        self.uncleared_rooms = [
            room for room in self.uncleared_rooms
            if abs(room[0] - position[0]) > radius or abs(room[1] - position[1]) > radius
        ]
    
    def get_all_uncleared(self) -> List[Tuple[int, int]]:
        """Get all uncleared room positions"""
        return self.uncleared_rooms.copy()

