"""
Simulation module: Main simulation controller
"""

from typing import Dict, List, Tuple, Optional
from src.environment import Environment
from src.agents import AgentManager, Evacuee, Responder
from src.hazards import HazardManager
from src.pathfinding import FlowField, RoomSweepPlanner


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
        self.flow_field = FlowField(env)
        self.sweep_planner = RoomSweepPlanner(env)
        
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
        """Initialize simulation (compute initial flow fields, assign tasks)"""
        # Compute initial flow field for evacuees
        self.flow_field.compute(self.env.exits, avoid_danger=True)
        
        # Assign initial tasks to responders
        for responder in self.agent_manager.responders:
            task = self.sweep_planner.assign_task(responder.get_position())
            if task:
                responder.assign_task(task, self.env)
    
    def step(self):
        """Execute one simulation timestep"""
        if not self.running:
            return
        
        self.timestep += 1
        
        # 1. Update hazards
        evacuee_positions = self.agent_manager.get_evacuee_positions()
        self.hazard_manager.update_all(self.env, self.timestep, evacuee_positions)
        
        # 2. Recompute flow field periodically
        if self.timestep % self.config.recompute_flow_interval == 0:
            self.flow_field.compute(self.env.exits, avoid_danger=True)
        
        # 3. Update responders
        for responder in self.agent_manager.responders:
            if not responder.active:
                continue
            
            # Move responder
            responder.update(self.env, self.agent_manager.evacuees)
            
            # Check if task completed
            if responder.has_reached_task():
                # Mark room as cleared
                if responder.current_task:
                    self.sweep_planner.mark_room_cleared(responder.current_task, radius=3)
                responder.clear_task()
                
                # Assign new task
                new_task = self.sweep_planner.assign_task(responder.get_position())
                if new_task:
                    responder.assign_task(new_task, self.env)
            
            # Replan if path blocked
            if self.timestep % self.config.replan_responder_interval == 0:
                responder.replan_path(self.env)
        
        # 4. Update evacuees
        for evacuee in self.agent_manager.evacuees:
            if evacuee.active and not evacuee.evacuated:
                evacuee.update(self.env, self.flow_field)
        
        # 5. Record frame
        self._record_frame()
        
        # 6. Check termination conditions
        self._check_termination()
    
    def _record_frame(self):
        """Record current state for export"""
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
                    'stuck': e.stuck,
                }
                for e in self.agent_manager.evacuees
            ],
            'danger_cells': self.env.get_danger_cells(),
            'grid': self.env.grid.copy(),
        }
        
        self.history.append(frame_data)
    
    def _check_termination(self):
        """Check if simulation should terminate"""
        # Terminate if max timesteps reached
        if self.timestep >= self.config.max_timesteps:
            self.running = False
            return
        
        # Terminate if all evacuees evacuated or stuck
        active_evacuees = self.agent_manager.count_active_evacuees()
        if active_evacuees == 0:
            self.running = False
            return
        
        # Terminate if all rooms cleared and no more active evacuees moving
        if not self.sweep_planner.get_all_uncleared():
            # Check if any evacuees made progress recently
            moving_evacuees = sum(1 for e in self.agent_manager.evacuees 
                                 if e.active and not e.evacuated and not e.stuck)
            if moving_evacuees == 0:
                self.running = False
    
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
                print(f"Timestep {self.timestep}: "
                      f"{self.agent_manager.count_evacuated()} evacuated, "
                      f"{self.agent_manager.count_active_evacuees()} active, "
                      f"{self.agent_manager.count_stuck()} stuck")
        
        # Finalize metrics
        self._compute_final_metrics()
        
        print(f"\nSimulation complete at timestep {self.timestep}")
        print(f"Evacuated: {self.metrics['evacuated_count']}")
        print(f"Rescued: {self.metrics['rescued_count']}")
        print(f"Stuck: {self.metrics['stuck_count']}")
        print(f"Evacuation rate: {self.metrics['evacuation_rate']:.1%}")
        print(f"Total responder distance: {self.metrics['responder_distance']}")
        
        return self.metrics
    
    def _compute_final_metrics(self):
        """Compute final simulation metrics"""
        total_evacuees = len(self.agent_manager.evacuees)
        
        self.metrics['total_time'] = self.timestep
        self.metrics['evacuated_count'] = self.agent_manager.count_evacuated()
        self.metrics['rescued_count'] = self.agent_manager.count_rescued()
        self.metrics['stuck_count'] = self.agent_manager.count_stuck()
        self.metrics['responder_distance'] = self.agent_manager.get_total_responder_distance()
        
        if total_evacuees > 0:
            self.metrics['evacuation_rate'] = self.metrics['evacuated_count'] / total_evacuees
        
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

