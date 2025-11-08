"""
Simulation module: Main simulation controller
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from src.environment import Environment
from src.agents import AgentManager, Evacuee, Responder
from src.hazards import HazardManager
from src.pathfinding import FlowField
from src.room_priority import RoomWeightCalculator


class SimulationConfig:
    """Configuration parameters for simulation"""
    
    def __init__(self):
        # Hazard parameters
        self.fire_spread_prob = 0.2
        self.gas_diffusion_rate = 0.1
        self.gas_faint_threshold = 0.5
        self.shooter_vision_radius = 5
        
        # Agent parameters
        self.responder_speed = 1.0
        self.evacuee_speed = 1.0
        self.escort_speed = 0.5
        
        # Simulation parameters
        self.max_timesteps = 1000
        self.recompute_flow_interval = 5  # Recompute evacuee paths every N steps
        self.replan_responder_interval = 10  # Replan responder paths every N steps
        
        # Success criteria
        self.min_evacuation_rate = 0.8  # Success if 80%+ evacuated


class Simulation:
    """Main simulation controller"""
    
    def __init__(self, env: Environment, config: Optional[SimulationConfig] = None):
        self.env = env
        self.config = config or SimulationConfig()
        
        self.agent_manager = AgentManager()
        self.hazard_manager = HazardManager()
        self.room_calculator = RoomWeightCalculator(env)  # TRP optimization
        
        self.timestep = 0
        self.running = True
        self.history = []  # Frame history for export
        
        # Metrics
        self.metrics = {
            'total_time': 0,
            'evacuated_count': 0,
            'rescued_count': 0,
            'stuck_count': 0,
            'responder_distance': 0,
            'hazard_coverage': 0.0,
            'evacuation_rate': 0.0,
        }
        
    def add_evacuees(self, positions: List[Tuple[int, int]]):
        """Add evacuees at specified positions"""
        for x, y in positions:
            self.agent_manager.add_evacuee(x, y, self.config.evacuee_speed)
    
    def add_responders(self, positions: List[Tuple[int, int]]):
        """Add responders at specified positions"""
        for x, y in positions:
            self.agent_manager.add_responder(x, y, self.config.responder_speed)
    
    def add_fire_hazard(self, origin: Tuple[int, int]):
        """Add fire hazard at origin"""
        self.hazard_manager.add_fire(origin, self.config.fire_spread_prob)
        self.env.mark_danger(origin[0], origin[1], 'fire', self.timestep)
    
    def add_gas_hazard(self, origin: Tuple[int, int]):
        """Add gas hazard at origin"""
        self.hazard_manager.add_gas(origin, self.config.gas_diffusion_rate,
                                    self.config.gas_faint_threshold)
    
    def add_shooter_hazard(self, start_pos: Tuple[int, int]):
        """Add shooter hazard at start position"""
        self.hazard_manager.add_shooter(start_pos, self.config.shooter_vision_radius)
        self.env.mark_danger(start_pos[0], start_pos[1], 'shooter', self.timestep)
    
    def initialize(self):
        """Initialize simulation (assign evacuees to rooms, assign initial tasks)"""
        # Assign evacuees to rooms
        for evacuee in self.agent_manager.evacuees:
            cell = self.env.get_cell(evacuee.x, evacuee.y)
            if cell:
                evacuee.room_id = cell.room_id
        
        # Update initial room states
        self.room_calculator.update_room_states(self.env, self.timestep)
        
        # Assign initial tasks to responders using TRP logic
        for responder in self.agent_manager.responders:
            next_room = self.room_calculator.get_next_room_priority(
                responder.get_position(),
                self.timestep,
                None  # path_finder not needed, handled internally
            )
            if next_room:
                responder.assign_room_task(next_room, self.env)
    
    def step(self):
        """Execute one simulation timestep with TRP optimization"""
        if not self.running:
            return
        
        self.timestep += 1
        
        # 1. Update hazards
        evacuee_positions = self.agent_manager.get_evacuee_positions()
        self.hazard_manager.update_all(self.env, self.timestep, evacuee_positions)
        
        # 2. Update room states (danger, time to untenability, accessibility)
        self.room_calculator.update_room_states(self.env, self.timestep)
        
        # 3. Update evacuees (static, but track danger exposure)
        for evacuee in self.agent_manager.evacuees:
            if evacuee.active and not evacuee.found:
                evacuee.update(self.env)
        
        # 4. Update responders using TRP optimization
        for responder in self.agent_manager.responders:
            if not responder.active:
                continue
            
            # Move responder
            responder.update(self.env, self.agent_manager.evacuees)
            
            # Check if reached current room
            if responder.has_reached_room(self.env):
                # Mark room as cleared
                if responder.current_room_target:
                    self.room_calculator.mark_room_cleared(responder.current_room_target.room_id)
                    responder.clear_room()
                
                # Assign new room using TRP weights
                next_room = self.room_calculator.get_next_room_priority(
                    responder.get_position(),
                    self.timestep,
                    None
                )
                if next_room:
                    responder.assign_room_task(next_room, self.env)
            
            # Replan if path blocked by hazards
            if self.timestep % self.config.replan_responder_interval == 0:
                responder.replan_path(self.env)
        
        # 5. Record frame
        self._record_frame()
        
        # 6. Check termination conditions
        self._check_termination()
    
    def _record_frame(self):
        """Record current state for export"""
        # Create danger level heatmap
        danger_heatmap = np.zeros((self.env.height, self.env.width))
        for y in range(self.env.height):
            for x in range(self.env.width):
                cell = self.env.get_cell(x, y)
                if cell:
                    danger_heatmap[y, x] = cell.danger_level
        
        frame_data = {
            'timestep': self.timestep,
            'responders': [
                {
                    'id': r.id,
                    'x': r.x,
                    'y': r.y,
                    'active': r.active,
                    'rescued_count': r.rescued_count,
                }
                for r in self.agent_manager.responders
            ],
            'evacuees': [
                {
                    'id': e.id,
                    'x': e.x,
                    'y': e.y,
                    'active': e.active,
                    'evacuated': e.evacuated,
                    'rescued': e.rescued,
                    'stuck': False,  # No longer used in static model
                    'unconscious': e.unconscious,
                    'found': e.found,
                }
                for e in self.agent_manager.evacuees
            ],
            'danger_cells': self.env.get_danger_cells(),
            'grid': self.env.grid.copy(),
            'danger_heatmap': danger_heatmap,
            'rooms_cleared': len([r for r in self.room_calculator.get_all_rooms() if r.is_cleared]),
            'total_rooms': len(self.room_calculator.get_all_rooms()),
        }
        
        self.history.append(frame_data)
    
    def _check_termination(self):
        """Check if simulation should terminate (TRP: all rooms cleared)"""
        # Terminate if max timesteps reached
        if self.timestep >= self.config.max_timesteps:
            self.running = False
            return
        
        # Terminate if all rooms have been cleared (sweep complete)
        uncleared_rooms = self.room_calculator.get_uncleared_rooms()
        accessible_uncleared = [r for r in uncleared_rooms if r.is_accessible]
        
        if len(accessible_uncleared) == 0:
            # All accessible rooms cleared - mission complete
            self.running = False
            return
        
        # Terminate if all evacuees found (optional early termination)
        unfound_evacuees = self.agent_manager.count_active_evacuees()
        if unfound_evacuees == 0 and len(uncleared_rooms) == 0:
            self.running = False
            return
    
    def run(self, max_steps: Optional[int] = None):
        """
        Run simulation until completion
        
        Args:
            max_steps: Override config max_timesteps if provided
        """
        if max_steps:
            self.config.max_timesteps = max_steps
        
        self.initialize()
        
        print(f"Starting simulation with {len(self.agent_manager.evacuees)} evacuees "
              f"and {len(self.agent_manager.responders)} responders")
        
        while self.running:
            self.step()
            
            # Print progress every 50 steps
            if self.timestep % 50 == 0:
                cleared = len([r for r in self.room_calculator.get_all_rooms() if r.is_cleared])
                total = len(self.room_calculator.get_all_rooms())
                found = self.agent_manager.count_rescued()
                unfound = self.agent_manager.count_active_evacuees()
                print(f"Timestep {self.timestep}: "
                      f"Rooms {cleared}/{total} cleared, "
                      f"{found} evacuees found, "
                      f"{unfound} unfound")
        
        # Finalize metrics
        self._compute_final_metrics()
        
        print(f"\nSimulation complete at timestep {self.timestep}")
        print(f"Rooms cleared: {self.metrics['rooms_cleared']}/{self.metrics['total_rooms']}")
        print(f"Evacuees found: {self.metrics['evacuees_found']}")
        print(f"Unconscious: {self.metrics['unconscious_count']}")
        print(f"Sweep completion: {self.metrics['sweep_completion_rate']:.1%}")
        print(f"Total responder distance: {self.metrics['responder_distance']}")
        
        return self.metrics
    
    def _compute_final_metrics(self):
        """Compute final simulation metrics (TRP focus)"""
        total_evacuees = len(self.agent_manager.evacuees)
        total_rooms = len(self.room_calculator.get_all_rooms())
        
        self.metrics['total_time'] = self.timestep
        self.metrics['evacuees_found'] = self.agent_manager.count_rescued()
        self.metrics['unconscious_count'] = self.agent_manager.count_unconscious()
        self.metrics['responder_distance'] = self.agent_manager.get_total_responder_distance()
        
        # Room sweep metrics
        cleared_rooms = len([r for r in self.room_calculator.get_all_rooms() if r.is_cleared])
        self.metrics['rooms_cleared'] = cleared_rooms
        self.metrics['total_rooms'] = total_rooms
        self.metrics['sweep_completion_rate'] = cleared_rooms / total_rooms if total_rooms > 0 else 0
        
        # Evacuee metrics
        if total_evacuees > 0:
            self.metrics['evacuee_found_rate'] = self.metrics['evacuees_found'] / total_evacuees
        else:
            self.metrics['evacuee_found_rate'] = 0
        
        # Calculate hazard coverage
        danger_cells = len(self.env.get_danger_cells())
        total_cells = self.env.width * self.env.height
        self.metrics['hazard_coverage'] = danger_cells / total_cells if total_cells > 0 else 0
    
    def get_history(self) -> List[Dict]:
        """Get simulation history for export"""
        return self.history
    
    def get_metrics(self) -> Dict:
        """Get simulation metrics"""
        return self.metrics.copy()

