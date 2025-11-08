"""
Environment module: Grid representation of building layouts
"""

import numpy as np
from enum import IntEnum
from typing import List, Tuple, Optional, Set


class CellState(IntEnum):
    """Cell state codes"""
    WALL = 0
    SAFE = 1
    EXIT = 2
    DANGER = 3
    RESPONDER = 4
    EVACUEE = 5


class Cell:
    """Represents a single grid cell with metadata"""
    
    def __init__(self, x: int, y: int, state: CellState = CellState.SAFE):
        self.x = x
        self.y = y
        self.state = state
        self.danger_time = None  # Timestep when cell became dangerous
        self.hazard_type = None  # 'fire', 'gas', or 'shooter'
        self.room_id = None
        self.gas_concentration = 0.0
        self.is_cleared = False  # For responder sweep tracking
        
    def __repr__(self):
        return f"Cell({self.x},{self.y},{self.state.name})"


class Environment:
    """Grid-based building environment"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = np.full((height, width), CellState.SAFE, dtype=int)
        self.cells = [[Cell(x, y) for x in range(width)] for y in range(height)]
        self.exits = []
        self.spawn_points = []
        
    def set_cell(self, x: int, y: int, state: CellState):
        """Set cell state"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y, x] = state
            self.cells[y][x].state = state
            
    def get_cell(self, x: int, y: int) -> Optional[Cell]:
        """Get cell object"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.cells[y][x]
        return None
    
    def get_state(self, x: int, y: int) -> Optional[CellState]:
        """Get cell state"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return CellState(self.grid[y, x])
        return None
    
    def is_walkable(self, x: int, y: int, can_cross_danger: bool = False) -> bool:
        """Check if cell is walkable"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        state = self.grid[y, x]
        if state == CellState.WALL:
            return False
        if state == CellState.DANGER and not can_cross_danger:
            return False
        return True
    
    def get_neighbors(self, x: int, y: int, can_cross_danger: bool = False) -> List[Tuple[int, int]]:
        """Get valid neighboring cells (4-directional)"""
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if self.is_walkable(nx, ny, can_cross_danger):
                neighbors.append((nx, ny))
        return neighbors
    
    def get_neighbors_8(self, x: int, y: int, can_cross_danger: bool = False) -> List[Tuple[int, int]]:
        """Get valid neighboring cells (8-directional including diagonals)"""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if self.is_walkable(nx, ny, can_cross_danger):
                    neighbors.append((nx, ny))
        return neighbors
    
    def mark_danger(self, x: int, y: int, hazard_type: str, timestep: int):
        """Mark cell as dangerous"""
        cell = self.get_cell(x, y)
        if cell and cell.state != CellState.WALL and cell.state != CellState.EXIT:
            self.set_cell(x, y, CellState.DANGER)
            cell.danger_time = timestep
            cell.hazard_type = hazard_type
    
    def add_exit(self, x: int, y: int):
        """Add an exit"""
        self.set_cell(x, y, CellState.EXIT)
        self.exits.append((x, y))
    
    def add_spawn_point(self, x: int, y: int):
        """Add evacuee spawn point"""
        self.spawn_points.append((x, y))
    
    def create_room(self, x1: int, y1: int, x2: int, y2: int, room_id: int, fill_walls: bool = True):
        """Create a rectangular room with walls"""
        # Create perimeter walls
        if fill_walls:
            for x in range(x1, x2 + 1):
                self.set_cell(x, y1, CellState.WALL)
                self.set_cell(x, y2, CellState.WALL)
            for y in range(y1, y2 + 1):
                self.set_cell(x1, y, CellState.WALL)
                self.set_cell(x2, y, CellState.WALL)
        
        # Mark interior cells with room_id
        for y in range(y1 + 1, y2):
            for x in range(x1 + 1, x2):
                cell = self.get_cell(x, y)
                if cell:
                    cell.room_id = room_id
    
    def create_door(self, x: int, y: int):
        """Create a door (opening in wall)"""
        self.set_cell(x, y, CellState.SAFE)
    
    def create_hallway(self, x1: int, y1: int, x2: int, y2: int):
        """Create a hallway between two points"""
        # Horizontal then vertical
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.set_cell(x, y1, CellState.SAFE)
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.set_cell(x2, y, CellState.SAFE)
    
    def get_all_safe_cells(self) -> List[Tuple[int, int]]:
        """Get all currently safe (non-wall, non-danger) cells"""
        safe_cells = []
        for y in range(self.height):
            for x in range(self.width):
                state = self.grid[y, x]
                if state in [CellState.SAFE, CellState.EXIT]:
                    safe_cells.append((x, y))
        return safe_cells
    
    def get_danger_cells(self) -> List[Tuple[int, int]]:
        """Get all dangerous cells"""
        danger_cells = []
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y, x] == CellState.DANGER:
                    danger_cells.append((x, y))
        return danger_cells
    
    def copy(self):
        """Create a deep copy of the environment"""
        new_env = Environment(self.width, self.height)
        new_env.grid = self.grid.copy()
        new_env.exits = self.exits.copy()
        new_env.spawn_points = self.spawn_points.copy()
        # Deep copy cells
        for y in range(self.height):
            for x in range(self.width):
                old_cell = self.cells[y][x]
                new_cell = new_env.cells[y][x]
                new_cell.state = old_cell.state
                new_cell.danger_time = old_cell.danger_time
                new_cell.hazard_type = old_cell.hazard_type
                new_cell.room_id = old_cell.room_id
                new_cell.gas_concentration = old_cell.gas_concentration
                new_cell.is_cleared = old_cell.is_cleared
        return new_env


def create_office_layout(width: int = 50, height: int = 50) -> Environment:
    """Create a simple office layout with hallway and rooms"""
    env = Environment(width, height)
    
    # Perimeter walls
    for x in range(width):
        env.set_cell(x, 0, CellState.WALL)
        env.set_cell(x, height - 1, CellState.WALL)
    for y in range(height):
        env.set_cell(0, y, CellState.WALL)
        env.set_cell(width - 1, y, CellState.WALL)
    
    # Central hallway
    hallway_y = height // 2
    for x in range(5, width - 5):
        env.set_cell(x, hallway_y, CellState.SAFE)
    
    # Create rooms along hallway
    room_width = 12
    room_height = 10
    room_id = 0
    
    # Top rooms
    for i in range(3):
        x_start = 8 + i * 15
        env.create_room(x_start, hallway_y - room_height - 2, 
                       x_start + room_width, hallway_y - 2, room_id)
        env.create_door(x_start + room_width // 2, hallway_y - 2)
        room_id += 1
    
    # Bottom rooms
    for i in range(3):
        x_start = 8 + i * 15
        env.create_room(x_start, hallway_y + 2, 
                       x_start + room_width, hallway_y + room_height + 2, room_id)
        env.create_door(x_start + room_width // 2, hallway_y + 2)
        room_id += 1
    
    # Add exits
    env.add_exit(5, hallway_y)
    env.add_exit(width - 6, hallway_y)
    
    # Add spawn points in rooms
    env.add_spawn_point(12, hallway_y - 6)
    env.add_spawn_point(27, hallway_y - 6)
    env.add_spawn_point(42, hallway_y - 6)
    env.add_spawn_point(12, hallway_y + 6)
    env.add_spawn_point(27, hallway_y + 6)
    env.add_spawn_point(42, hallway_y + 6)
    
    return env


def create_school_layout(width: int = 60, height: int = 60) -> Environment:
    """Create a school layout with multiple classrooms"""
    env = Environment(width, height)
    
    # Perimeter walls
    for x in range(width):
        env.set_cell(x, 0, CellState.WALL)
        env.set_cell(x, height - 1, CellState.WALL)
    for y in range(height):
        env.set_cell(0, y, CellState.WALL)
        env.set_cell(width - 1, y, CellState.WALL)
    
    # Main hallways (cross pattern)
    hallway_v = width // 2
    hallway_h = height // 2
    
    for x in range(5, width - 5):
        env.set_cell(x, hallway_h, CellState.SAFE)
    for y in range(5, height - 5):
        env.set_cell(hallway_v, y, CellState.SAFE)
    
    # Classrooms in four quadrants
    room_id = 0
    classroom_size = 12
    
    # Top-left classrooms
    env.create_room(8, 8, 8 + classroom_size, 8 + classroom_size, room_id)
    env.create_door(8 + classroom_size // 2, 8 + classroom_size)
    env.add_spawn_point(12, 12)
    room_id += 1
    
    # Top-right classrooms
    env.create_room(width - 8 - classroom_size, 8, width - 8, 8 + classroom_size, room_id)
    env.create_door(width - 8 - classroom_size // 2, 8 + classroom_size)
    env.add_spawn_point(width - 12, 12)
    room_id += 1
    
    # Bottom-left classrooms
    env.create_room(8, height - 8 - classroom_size, 8 + classroom_size, height - 8, room_id)
    env.create_door(8 + classroom_size // 2, height - 8 - classroom_size)
    env.add_spawn_point(12, height - 12)
    room_id += 1
    
    # Bottom-right classrooms
    env.create_room(width - 8 - classroom_size, height - 8 - classroom_size, 
                   width - 8, height - 8, room_id)
    env.create_door(width - 8 - classroom_size // 2, height - 8 - classroom_size)
    env.add_spawn_point(width - 12, height - 12)
    room_id += 1
    
    # Add exits at hallway ends
    env.add_exit(hallway_v, 5)
    env.add_exit(hallway_v, height - 6)
    env.add_exit(5, hallway_h)
    env.add_exit(width - 6, hallway_h)
    
    return env

