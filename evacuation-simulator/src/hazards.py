"""
Hazards module: Fire spread, gas diffusion, and shooter movement logic
"""

import numpy as np
from typing import List, Tuple, Optional
import random
from src.environment import Environment, CellState


class Fire:
    """Fire hazard that spreads radially with heat/smoke intensity"""
    
    def __init__(self, origin: Tuple[int, int], spread_prob: float = 0.2, heat_radius: int = 5):
        self.origin = origin
        self.spread_prob = spread_prob
        self.heat_radius = heat_radius
        self.burning_cells = {origin}  # Actual flames
        
    def spread(self, env: Environment, timestep: int):
        """Spread fire to adjacent cells and update heat/smoke danger levels"""
        new_burns = set()
        
        # Spread flames to neighbors
        for x, y in list(self.burning_cells):
            for nx, ny in env.get_neighbors(x, y, can_cross_danger=True):
                if (nx, ny) not in self.burning_cells:
                    state = env.get_state(nx, ny)
                    if state not in [CellState.WALL, CellState.EXIT]:
                        if random.random() < self.spread_prob:
                            new_burns.add((nx, ny))
        
        self.burning_cells.update(new_burns)
        
        # Update heat/smoke danger levels for all cells based on distance from fires
        for y in range(env.height):
            for x in range(env.width):
                if env.get_state(x, y) == CellState.WALL:
                    continue
                
                # Calculate danger based on nearest fire
                min_distance = float('inf')
                for fx, fy in self.burning_cells:
                    distance = ((x - fx)**2 + (y - fy)**2) ** 0.5
                    min_distance = min(min_distance, distance)
                
                if min_distance <= self.heat_radius:
                    # Danger falls off with distance: 1.0 at fire, ~0.2 at radius edge
                    danger_level = max(0.0, 1.0 - (min_distance / self.heat_radius) * 0.8)
                    cell = env.get_cell(x, y)
                    if cell:
                        cell.fire_intensity = danger_level
                        env.mark_danger(x, y, 'fire', timestep, danger_level)
        
        return new_burns


class Gas:
    """Gas hazard that diffuses throughout the building"""
    
    def __init__(self, origin: Tuple[int, int], diffusion_rate: float = 0.1, 
                 faint_threshold: float = 0.5):
        self.origin = origin
        self.diffusion_rate = diffusion_rate
        self.faint_threshold = faint_threshold
        
    def diffuse(self, env: Environment, timestep: int):
        """Diffuse gas concentration across the grid"""
        # Create concentration matrix
        new_concentrations = np.zeros((env.height, env.width))
        
        # Copy current concentrations
        for y in range(env.height):
            for x in range(env.width):
                cell = env.get_cell(x, y)
                if cell:
                    new_concentrations[y, x] = cell.gas_concentration
        
        # Source point keeps producing gas
        origin_cell = env.get_cell(self.origin[0], self.origin[1])
        if origin_cell:
            origin_cell.gas_concentration = min(1.0, origin_cell.gas_concentration + 0.2)
        
        # Diffusion step: spread to neighbors
        diffused = np.zeros((env.height, env.width))
        
        for y in range(env.height):
            for x in range(env.width):
                if env.get_state(x, y) == CellState.WALL:
                    continue
                    
                cell = env.get_cell(x, y)
                current_conc = cell.gas_concentration
                
                # Get neighbors
                neighbors = env.get_neighbors(x, y, can_cross_danger=True)
                
                if neighbors:
                    # Diffuse to neighbors
                    diffusion_amount = current_conc * self.diffusion_rate / len(neighbors)
                    
                    for nx, ny in neighbors:
                        neighbor_cell = env.get_cell(nx, ny)
                        if neighbor_cell:
                            diffused[ny, nx] += diffusion_amount
                    
                    # Keep remaining concentration
                    diffused[y, x] += current_conc * (1 - self.diffusion_rate)
        
        # Update concentrations and danger levels
        affected_cells = []
        for y in range(env.height):
            for x in range(env.width):
                cell = env.get_cell(x, y)
                if cell and env.get_state(x, y) != CellState.WALL:
                    cell.gas_concentration = diffused[y, x]
                    
                    # Danger level equals gas concentration (already 0-1)
                    danger_level = cell.gas_concentration
                    if danger_level > 0.1:  # Only mark if significant
                        env.mark_danger(x, y, 'gas', timestep, danger_level)
                        affected_cells.append((x, y))
        
        return affected_cells


class Shooter:
    """Active shooter that moves intelligently toward evacuees"""
    
    def __init__(self, start_pos: Tuple[int, int], vision_radius: int = 5):
        self.x, self.y = start_pos
        self.vision_radius = vision_radius
        self.path_history = [start_pos]
        self.cells_threatened = set()
        
    def get_position(self) -> Tuple[int, int]:
        return (self.x, self.y)
    
    def can_see(self, target_x: int, target_y: int) -> bool:
        """Check if shooter can see target position (simple distance check)"""
        dx = target_x - self.x
        dy = target_y - self.y
        distance = (dx * dx + dy * dy) ** 0.5
        return distance <= self.vision_radius
    
    def move(self, env: Environment, evacuee_positions: List[Tuple[int, int]], 
             timestep: int):
        """
        Move shooter based on random walk biased toward visible evacuees
        Updates danger gradient based on proximity
        """
        # Check for visible evacuees
        visible_evacuees = []
        for ex, ey in evacuee_positions:
            if self.can_see(ex, ey):
                visible_evacuees.append((ex, ey))
        
        # Get valid neighbors
        neighbors = env.get_neighbors(self.x, self.y, can_cross_danger=True)
        
        if not neighbors:
            return  # Stuck
        
        # If evacuees visible, move toward closest one
        if visible_evacuees:
            closest = min(visible_evacuees, 
                         key=lambda e: (e[0] - self.x)**2 + (e[1] - self.y)**2)
            best_move = min(neighbors, 
                           key=lambda n: (n[0] - closest[0])**2 + (n[1] - closest[1])**2)
            self.x, self.y = best_move
        else:
            # Random walk
            self.x, self.y = random.choice(neighbors)
        
        self.path_history.append((self.x, self.y))
        
        # Update danger gradient around shooter
        for dy in range(-self.vision_radius, self.vision_radius + 1):
            for dx in range(-self.vision_radius, self.vision_radius + 1):
                tx, ty = self.x + dx, self.y + dy
                if 0 <= tx < env.width and 0 <= ty < env.height:
                    state = env.get_state(tx, ty)
                    if state not in [CellState.WALL, CellState.EXIT]:
                        distance = (dx*dx + dy*dy) ** 0.5
                        if distance <= self.vision_radius:
                            # Danger gradient: 1.0 at shooter, falls off with distance
                            # 1.0 at position, 0.8 nearby, 0.4-0.6 within sight
                            if distance == 0:
                                danger_level = 1.0
                            elif distance <= 2:
                                danger_level = 0.9
                            elif distance <= 4:
                                danger_level = 0.7
                            else:
                                danger_level = 0.4 + 0.3 * (1.0 - distance / self.vision_radius)
                            
                            env.mark_danger(tx, ty, 'shooter', timestep, danger_level)
                            self.cells_threatened.add((tx, ty))


class HazardManager:
    """Manages all hazards in the simulation"""
    
    def __init__(self):
        self.hazards = []
        
    def add_fire(self, origin: Tuple[int, int], spread_prob: float = 0.2):
        """Add a fire hazard"""
        fire = Fire(origin, spread_prob)
        self.hazards.append(fire)
        return fire
    
    def add_gas(self, origin: Tuple[int, int], diffusion_rate: float = 0.1, 
                faint_threshold: float = 0.5):
        """Add a gas hazard"""
        gas = Gas(origin, diffusion_rate, faint_threshold)
        self.hazards.append(gas)
        return gas
    
    def add_shooter(self, start_pos: Tuple[int, int], vision_radius: int = 5):
        """Add a shooter hazard"""
        shooter = Shooter(start_pos, vision_radius)
        self.hazards.append(shooter)
        return shooter
    
    def update_all(self, env: Environment, timestep: int, 
                   evacuee_positions: List[Tuple[int, int]] = None):
        """Update all hazards"""
        if evacuee_positions is None:
            evacuee_positions = []
            
        for hazard in self.hazards:
            if isinstance(hazard, Fire):
                hazard.spread(env, timestep)
            elif isinstance(hazard, Gas):
                hazard.diffuse(env, timestep)
            elif isinstance(hazard, Shooter):
                hazard.move(env, evacuee_positions, timestep)
    
    def get_all_danger_cells(self) -> List[Tuple[int, int]]:
        """Get all cells affected by any hazard"""
        danger_cells = set()
        for hazard in self.hazards:
            if isinstance(hazard, Fire):
                danger_cells.update(hazard.burning_cells)
            elif isinstance(hazard, Shooter):
                danger_cells.update(hazard.cells_threatened)
        return list(danger_cells)

