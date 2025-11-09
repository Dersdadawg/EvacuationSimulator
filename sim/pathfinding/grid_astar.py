"""A* pathfinding on 0.5m grid avoiding walls and danger"""

import heapq
import numpy as np
from typing import List, Tuple, Set, Dict, Optional


class GridPathfinder:
    """A* pathfinding on grid that avoids walls and high-danger cells"""
    
    def __init__(self, environment, hazard_system):
        self.env = environment
        self.hazard_system = hazard_system
        self.grid_res = 0.5
        
        # Build wall cell set
        self._build_wall_cells()
    
    def _build_wall_cells(self):
        """Identify which cells are walls (cannot be traversed)"""
        self.wall_cells: Set[Tuple[float, float]] = set()
        
        layout = self.env.layout
        
        # For each office, mark perimeter cells as walls (except doors)
        for room_data in layout.get('rooms', []):
            room_type = room_data.get('type', 'office')
            if room_type == 'hallway' or room_data.get('is_exit'):
                continue  # No walls around hallway/exits
            
            room_id = room_data['id']
            x_center = room_data['x']
            y_center = room_data['y']
            w = room_data['width']
            h = room_data['height']
            
            x1, y1 = x_center - w/2, y_center - h/2
            x2, y2 = x_center + w/2, y_center + h/2
            
            # Find door location
            door_on_top = False
            door_on_bottom = False
            
            for conn in layout.get('connections', []):
                if room_id in [conn['from'], conn['to']]:
                    other = conn['to'] if conn['from'] == room_id else conn['from']
                    other_room = next((r for r in layout.get('rooms', []) if r['id'] == other), None)
                    if other_room and other_room.get('type') == 'hallway':
                        hallway_y = other_room['y']
                        if hallway_y < y_center:
                            door_on_top = True
                        else:
                            door_on_bottom = True
            
            door_width = 2.0  # 2m door
            
            # Mark TOP wall cells
            x = x1
            while x <= x2:
                cell_x = int(x / self.grid_res) * self.grid_res + 0.25
                cell_y = int(y1 / self.grid_res) * self.grid_res + 0.25
                
                # Skip door opening
                if door_on_top:
                    if abs(cell_x - x_center) <= door_width / 2:
                        x += self.grid_res
                        continue
                
                self.wall_cells.add((cell_x, cell_y))
                x += self.grid_res
            
            # Mark BOTTOM wall cells
            x = x1
            while x <= x2:
                cell_x = int(x / self.grid_res) * self.grid_res + 0.25
                cell_y = int(y2 / self.grid_res) * self.grid_res + 0.25
                
                # Skip door opening
                if door_on_bottom:
                    if abs(cell_x - x_center) <= door_width / 2:
                        x += self.grid_res
                        continue
                
                self.wall_cells.add((cell_x, cell_y))
                x += self.grid_res
            
            # Mark LEFT wall cells
            y = y1
            while y <= y2:
                cell_x = int(x1 / self.grid_res) * self.grid_res + 0.25
                cell_y = int(y / self.grid_res) * self.grid_res + 0.25
                self.wall_cells.add((cell_x, cell_y))
                y += self.grid_res
            
            # Mark RIGHT wall cells
            y = y1
            while y <= y2:
                cell_x = int(x2 / self.grid_res) * self.grid_res + 0.25
                cell_y = int(y / self.grid_res) * self.grid_res + 0.25
                self.wall_cells.add((cell_x, cell_y))
                y += self.grid_res
    
    def find_path(self, start_x: float, start_y: float, 
                  goal_x: float, goal_y: float,
                  avoid_danger: bool = True,
                  danger_threshold: float = 0.8) -> Optional[List[Tuple[float, float]]]:
        """
        Find path using A* on grid, avoiding walls and optionally danger
        
        Args:
            start_x, start_y: Starting position
            goal_x, goal_y: Goal position
            avoid_danger: If True, avoid high-danger cells
            danger_threshold: Avoid cells with danger > this value
            
        Returns:
            List of (x, y) waypoints, or None if no path
        """
        # Convert to grid cells
        start_cell = (
            int(start_x / self.grid_res) * self.grid_res + 0.25,
            int(start_y / self.grid_res) * self.grid_res + 0.25
        )
        goal_cell = (
            int(goal_x / self.grid_res) * self.grid_res + 0.25,
            int(goal_y / self.grid_res) * self.grid_res + 0.25
        )
        
        # Find nearest valid cells if start/goal are invalid
        if start_cell not in self.hazard_system.cells or start_cell in self.wall_cells:
            start_cell = self._find_nearest_valid_cell(start_x, start_y)
            if not start_cell:
                return None
        
        if goal_cell not in self.hazard_system.cells or goal_cell in self.wall_cells:
            goal_cell = self._find_nearest_valid_cell(goal_x, goal_y)
            if not goal_cell:
                return None
        
        # A* algorithm
        open_set = []
        heapq.heappush(open_set, (0, start_cell))
        
        came_from: Dict[Tuple[float, float], Tuple[float, float]] = {}
        g_score: Dict[Tuple[float, float], float] = {start_cell: 0}
        f_score: Dict[Tuple[float, float], float] = {start_cell: self._heuristic(start_cell, goal_cell)}
        
        closed_set: Set[Tuple[float, float]] = set()
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == goal_cell:
                # Reconstruct path
                return self._reconstruct_path(came_from, current)
            
            if current in closed_set:
                continue
            
            closed_set.add(current)
            
            # Check neighbors (8-connected for diagonal movement!)
            for dx, dy in [(self.grid_res, 0), (-self.grid_res, 0), 
                          (0, self.grid_res), (0, -self.grid_res),
                          (self.grid_res, self.grid_res), (self.grid_res, -self.grid_res),
                          (-self.grid_res, self.grid_res), (-self.grid_res, -self.grid_res)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Check if neighbor is valid
                if not self._is_valid_cell(neighbor, avoid_danger, danger_threshold):
                    continue
                
                if neighbor in closed_set:
                    continue
                
                # Calculate cost
                tentative_g = g_score[current] + self._edge_cost(current, neighbor, avoid_danger)
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, goal_cell)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return None  # No path found
    
    def _find_nearest_valid_cell(self, x: float, y: float) -> Optional[Tuple[float, float]]:
        """Find nearest valid (non-wall, existing) cell to given position"""
        best_cell = None
        best_dist = float('inf')
        
        # Search nearby cells
        for cell_pos in self.hazard_system.cells.keys():
            if cell_pos in self.wall_cells:
                continue
            
            dist = abs(cell_pos[0] - x) + abs(cell_pos[1] - y)
            if dist < best_dist:
                best_dist = dist
                best_cell = cell_pos
        
        return best_cell
    
    def _is_valid_cell(self, cell: Tuple[float, float], 
                       avoid_danger: bool, danger_threshold: float) -> bool:
        """Check if cell can be traversed"""
        # Cannot traverse wall cells
        if cell in self.wall_cells:
            return False
        
        # Must be a valid grid cell
        if not hasattr(self.hazard_system, 'cells'):
            return True
        
        if cell not in self.hazard_system.cells:
            return False
        
        # Optionally avoid high-danger cells
        if avoid_danger:
            grid_cell = self.hazard_system.cells[cell]
            if grid_cell.is_burning:
                return False  # Never enter burning cells
            if grid_cell.danger_level > danger_threshold:
                return False  # Avoid high danger
        
        return True
    
    def _edge_cost(self, from_cell: Tuple[float, float], 
                   to_cell: Tuple[float, float], avoid_danger: bool) -> float:
        """Calculate cost of moving from one cell to another"""
        # Calculate actual distance (diagonal = sqrt(2) * grid_res)
        dx = abs(to_cell[0] - from_cell[0])
        dy = abs(to_cell[1] - from_cell[1])
        if dx > 0 and dy > 0:
            base_cost = 1.414 * self.grid_res  # Diagonal
        else:
            base_cost = self.grid_res  # Straight
        
        # Add danger penalty
        if avoid_danger and hasattr(self.hazard_system, 'cells'):
            if to_cell in self.hazard_system.cells:
                cell = self.hazard_system.cells[to_cell]
                danger_penalty = cell.danger_level * 10.0  # Higher danger = higher cost
                return base_cost + danger_penalty
        
        return base_cost
    
    def _heuristic(self, cell1: Tuple[float, float], 
                   cell2: Tuple[float, float]) -> float:
        """Manhattan distance heuristic"""
        return abs(cell1[0] - cell2[0]) + abs(cell1[1] - cell2[1])
    
    def _reconstruct_path(self, came_from: Dict, current: Tuple[float, float]) -> List[Tuple[float, float]]:
        """Reconstruct path from came_from map"""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

