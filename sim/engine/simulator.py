"""Main simulation engine with tick loop"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Callable
import numpy as np

from ..env.environment import Environment
from ..agents.agent_manager import AgentManager
from ..agents.agent import Agent, AgentState
from ..policy.decision_engine import DecisionEngine
from ..pathfinding.grid_astar import GridPathfinder


class EventType(Enum):
    """Types of simulation events"""
    AGENT_MOVE = "agent_move"
    AGENT_ARRIVE = "agent_arrive"
    ROOM_SEARCH_START = "room_search_start"
    ROOM_CLEARED = "room_cleared"
    EVACUEE_FOUND = "evacuee_found"
    EVACUEE_RESCUED = "evacuee_rescued"
    AGENT_QUEUED = "agent_queued"
    LATENCY_SPIKE = "latency_spike"
    SIMULATION_END = "simulation_end"


@dataclass
class SimulationEvent:
    """Represents a simulation event"""
    tick: int
    time: float
    event_type: EventType
    agent_id: Optional[int]
    room_id: Optional[str]
    data: dict
    
    def __repr__(self):
        return (f"Event(t={self.tick}, {self.event_type.value}, "
                f"agent={self.agent_id}, room={self.room_id})")


class Simulator:
    """Main simulation engine"""
    
    def __init__(self, environment: Environment, params: dict):
        """
        Initialize simulator
        
        Args:
            environment: Building environment
            params: Full simulation parameters
        """
        self.env = environment
        self.params = params
        
        # Core components
        self.agent_manager = AgentManager(environment, params.get('agents', {}))
        self.decision_engine = DecisionEngine(environment, params.get('policy', {}))
        self.decision_engine.set_agent_params(params.get('agents', {}))
        
        # Grid-based pathfinding (avoids walls and danger)
        if hasattr(environment.hazard_system, 'cells'):
            self.grid_pathfinder = GridPathfinder(environment, environment.hazard_system)
        else:
            self.grid_pathfinder = None
        
        # Simulation state
        self.tick = 0
        self.time = 0.0
        self.dt = params.get('simulation', {}).get('tick_duration', 1.0)
        self.time_cap = params.get('simulation', {}).get('time_cap', 600)
        self.running = False
        self.complete = False
        
        # Event log
        self.events: List[SimulationEvent] = []
        self.event_callbacks: List[Callable[[SimulationEvent], None]] = []
        
        # Random seed
        seed = params.get('simulation', {}).get('random_seed', 42)
        np.random.seed(seed)
        
        # Latency parameters
        self.latency_enabled = params.get('latency', {}).get('enabled', False)
        self.comm_delay_mean = params.get('latency', {}).get('comm_delay_mean', 1.0)
        self.comm_delay_std = params.get('latency', {}).get('comm_delay_std', 0.5)
    
    def add_event_callback(self, callback: Callable[[SimulationEvent], None]):
        """Register callback for events"""
        self.event_callbacks.append(callback)
    
    def log_event(self, event_type: EventType, agent_id: Optional[int] = None,
                  room_id: Optional[str] = None, data: dict = None):
        """Log a simulation event"""
        event = SimulationEvent(
            tick=self.tick,
            time=self.time,
            event_type=event_type,
            agent_id=agent_id,
            room_id=room_id,
            data=data or {}
        )
        self.events.append(event)
        
        # Notify callbacks
        for callback in self.event_callbacks:
            callback(event)
    
    def step(self):
        """Execute one simulation step"""
        # 1. Update hazards
        self.env.update_hazards(self.tick, self.dt)
        
        # 2. Check agent safety (d_c > 0.95 = death)
        self._check_agent_safety()
        
        # 3. Process each agent
        for agent in self.agent_manager.agents:
            if not agent.is_dead and not agent.escaped:  # Don't process dead or escaped agents
                self._process_agent(agent)
        
        # 4. Check completion
        self._check_completion()
        
        # 5. Increment time
        self.tick += 1
        self.time += self.dt
    
    def _check_agent_safety(self):
        """Check if any agents are in lethal danger (d_c > 0.95 OR burning cell)"""
        if hasattr(self.env.hazard_system, 'cells'):
            for agent in self.agent_manager.agents:
                if agent.is_dead:
                    continue
                
                # Find cell at agent's position (cells centered at 0.25, 0.75, 1.25, etc.)
                cell_x = int(agent.x / 0.5) * 0.5 + 0.25
                cell_y = int(agent.y / 0.5) * 0.5 + 0.25
                cell_pos = (cell_x, cell_y)
                
                if cell_pos in self.env.hazard_system.cells:
                    cell = self.env.hazard_system.cells[cell_pos]
                    # Die if danger > 0.95 OR in burning cell
                    if cell.danger_level > 0.95 or cell.is_burning:
                        agent.is_dead = True
                        agent.state = AgentState.IDLE  # Stop moving
                        print(f'[DEATH] Agent {agent.id} died at ({agent.x:.1f}, {agent.y:.1f}) - d_c={cell.danger_level:.2f}, burning={cell.is_burning}')
                        self.log_event(EventType.SIMULATION_END, agent.id, agent.current_room,
                                     {'reason': 'agent_death', 'danger': cell.danger_level, 'burning': cell.is_burning})
    
    def _process_agent(self, agent: Agent):
        """Process one agent for this tick"""
        
        if agent.state == AgentState.IDLE:
            # Agent needs new assignment
            self._assign_agent_target(agent)
        
        elif agent.state == AgentState.MOVING:
            # Agent is moving to next room in path
            self._process_movement(agent)
        
        elif agent.state == AgentState.SEARCHING:
            # Agent is searching current room
            self._process_searching(agent)
        
        elif agent.state == AgentState.DRAGGING:
            # Agent is dragging evacuee to exit
            self._process_dragging(agent)
        
        elif agent.state == AgentState.QUEUED:
            # Agent is waiting for stair
            self._process_queued(agent)
        
        # Accumulate hazard exposure
        current_room = self.env.rooms[agent.current_room]
        agent.accumulate_hazard_exposure(current_room.hazard, self.dt)
    
    def _assign_agent_target(self, agent: Agent):
        """Assign next target room to idle agent using grid pathfinding"""
        # Use grid pathfinding to find safe path to highest priority room
        if self.grid_pathfinder:
            uncleared_rooms = self.env.get_uncleared_rooms()
            
            best_room = None
            best_priority = -1
            best_path = None
            
            for room_id in uncleared_rooms:
                priority = self.decision_engine.calculate_priority_index(room_id, agent.current_room)
                if priority > best_priority:
                    target_room = self.env.rooms[room_id]
                    # Find grid path avoiding danger
                    grid_path = self.grid_pathfinder.find_path(
                        agent.x, agent.y, target_room.x, target_room.y,
                        avoid_danger=True, danger_threshold=0.8
                    )
                    if grid_path and len(grid_path) > 1:
                        best_priority = priority
                        best_room = room_id
                        best_path = grid_path
            
            if best_room and best_path:
                agent.target_room = best_room
                agent.waypoints = best_path
                agent.current_waypoint = 0
                agent.state = AgentState.MOVING
                self.log_event(EventType.AGENT_MOVE, agent.id, agent.current_room,
                             {'target': best_room, 'priority': best_priority})
            else:
                # No rescuable rooms! Agent should escape to nearest exit
                self._assign_escape_route(agent)
        else:
            # Fallback to room-based
            room_score = self.decision_engine.select_next_room(agent)
            if room_score:
                agent.set_target(room_score.room_id, room_score.path)
                self.log_event(EventType.AGENT_MOVE, agent.id, agent.current_room,
                             {'target': room_score.room_id, 'score': room_score.score})
    
    def _assign_escape_route(self, agent: Agent):
        """Route agent to nearest exit when no more rescues possible"""
        if not self.grid_pathfinder:
            return
        
        nearest_exit = None
        min_dist = float('inf')
        best_path = None
        
        for exit_id in self.env.exits:
            exit_room = self.env.rooms[exit_id]
            # Try to find a safe path to exit
            grid_path = self.grid_pathfinder.find_path(
                agent.x, agent.y, exit_room.x, exit_room.y,
                avoid_danger=True, danger_threshold=0.85  # Be more cautious when escaping
            )
            if grid_path and len(grid_path) > 1:
                dist = len(grid_path)
                if dist < min_dist:
                    min_dist = dist
                    nearest_exit = exit_id
                    best_path = grid_path
        
        if nearest_exit and best_path:
            agent.target_room = nearest_exit
            agent.waypoints = best_path
            agent.current_waypoint = 0
            agent.state = AgentState.ESCAPING
            self.log_event(EventType.AGENT_MOVE, agent.id, agent.current_room,
                         {'target': nearest_exit, 'action': 'escaping'})
    
    def _process_movement(self, agent: Agent):
        """Process agent movement along grid waypoints or room path"""
        # Use grid waypoints if available
        if agent.waypoints and self.grid_pathfinder:
            self._process_grid_movement(agent)
        elif agent.path and agent.path_index < len(agent.path):
            self._process_room_movement(agent)
        else:
            # Arrived at target
            self._handle_arrival(agent)
    
    def _process_grid_movement(self, agent: Agent):
        """Move agent along grid waypoints (cell-by-cell)"""
        if agent.current_waypoint >= len(agent.waypoints):
            # Reached goal
            self._handle_arrival(agent)
            return
        
        # Get next waypoint
        target_cell = agent.waypoints[agent.current_waypoint]
        target_x, target_y = target_cell
        
        # Move towards waypoint
        speed = agent.speed_drag if agent.carrying_evacuee else agent.speed_hall
        reached = agent.move_towards(target_x, target_y, speed, self.dt)
        
        if reached:
            agent.current_waypoint += 1
            # Update current room based on position
            room = self.env.get_room_at_position(agent.x, agent.y, agent.floor)
            if room:
                agent.current_room = room.id
    
    def _process_room_movement(self, agent: Agent):
        """Process agent movement along room path (old system fallback)"""
        if not agent.path or agent.path_index >= len(agent.path):
            # Arrived at target
            self._handle_arrival(agent)
            return
        
        # Get next room in path
        next_room_id = agent.path[agent.path_index]
        current_room_id = agent.current_room
        
        # Check if moving through stair
        if self.env.graph.has_edge(current_room_id, next_room_id):
            edge = self.env.graph[current_room_id][next_room_id]
            is_stair = edge.get('is_stair', False)
            
            if is_stair:
                # Check stair availability
                stair_id = current_room_id if self.env.rooms[current_room_id].is_stair else next_room_id
                
                if not self.agent_manager.is_stair_available(stair_id, agent.id):
                    # Queue for stair
                    self.agent_manager.enqueue_for_stair(stair_id, agent.id)
                    self.log_event(EventType.AGENT_QUEUED, agent.id, stair_id)
                    return
                else:
                    self.agent_manager.occupy_stair(stair_id, agent.id)
        
        # Set up target if not already moving to this room
        if not agent.moving_to_room:
            next_room = self.env.rooms[next_room_id]
            agent.target_x = next_room.x
            agent.target_y = next_room.y
            agent.moving_to_room = True
        
        # Interpolate movement towards target
        next_room = self.env.rooms[next_room_id]
        speed = agent.speed_drag if agent.carrying_evacuee else agent.speed_hall
        if self.env.graph.has_edge(current_room_id, next_room_id):
            edge = self.env.graph[current_room_id][next_room_id]
            if edge.get('is_stair', False):
                speed = agent.speed_stairs
        
        # Move towards target
        reached = agent.move_towards(agent.target_x, agent.target_y, speed, self.dt)
        
        if reached:
            # Arrived at next room
            agent.update_position(next_room.x, next_room.y, next_room.floor, next_room_id)
            agent.advance_path()
            agent.moving_to_room = False
            
            # Release previous stair if applicable
            current_room = self.env.rooms[current_room_id]
            if current_room.is_stair:
                self.agent_manager.release_stair(current_room_id)
            
            self.log_event(EventType.AGENT_MOVE, agent.id, next_room_id)
            
            # Check if arrived at target
            if agent.path_index >= len(agent.path):
                self._handle_arrival(agent)
    
    def _handle_arrival(self, agent: Agent):
        """Handle agent arriving at target room"""
        target_room = self.env.rooms[agent.target_room]
        
        self.log_event(EventType.AGENT_ARRIVE, agent.id, agent.target_room)
        
        # Check if agent is escaping and reached an exit
        if agent.state == AgentState.ESCAPING and target_room.is_exit:
            agent.escaped = True
            agent.state = AgentState.IDLE  # Mark as safe/idle
            agent.clear_target()
            self.log_event(EventType.AGENT_MOVE, agent.id, agent.target_room,
                         {'action': 'escaped_safely'})
            return
        
        # Check if this is exit delivery
        if target_room.is_exit and agent.carrying_evacuee:
            # Calculate priority of rescued evacuee's room
            rescue_priority = 0.0
            if agent.evacuee_source_room:
                rescue_priority = self.decision_engine.calculate_priority_index(
                    agent.evacuee_source_room, agent.current_room
                )
            
            # Log rescue with priority for success rate calculation
            self.log_event(EventType.EVACUEE_RESCUED, agent.id, agent.target_room,
                         {'source_room': agent.evacuee_source_room, 'priority': rescue_priority})
            
            # Complete rescue and increment count
            agent.evacuees_rescued += 1
            agent.carrying_evacuee = False
            agent.evacuee_source_room = None
            agent.state = AgentState.IDLE
            agent.clear_target()
            # Agent becomes idle - will get new assignment next tick
        
        # Check if room needs searching
        elif not target_room.cleared and not target_room.is_exit:
            service_time = self.decision_engine.estimate_service_time(agent.target_room)
            agent.start_searching(service_time)
            self.log_event(EventType.ROOM_SEARCH_START, agent.id, agent.target_room,
                         {'service_time': service_time})
        else:
            # Room already cleared or is special room
            agent.clear_target()
    
    def _process_searching(self, agent: Agent):
        """Process agent searching a room"""
        agent.time_remaining_action -= self.dt
        agent.time_in_current_state += self.dt
        
        if agent.time_remaining_action <= 0:
            # Search complete
            room = self.env.rooms[agent.current_room]
            room.mark_cleared(self.tick)
            agent.complete_search()
            
            # Discover evacuees
            evac_count = room.discover_evacuees()
            
            self.log_event(EventType.ROOM_CLEARED, agent.id, agent.current_room,
                         {'evacuees_found': evac_count})
            
            if evac_count > 0:
                # Found evacuees - log discovery
                self.log_event(EventType.EVACUEE_FOUND, agent.id, agent.current_room,
                             {'count': evac_count})
            
            # Check if evacuees remaining (this agent or others may pick up)
            if room.evacuees_remaining > 0:
                # Pick up ONE evacuee (each agent picks up one)
                room.rescue_evacuee()  # Decrement count immediately
                agent.carrying_evacuee = True
                agent.evacuee_source_room = agent.current_room
                
                # Get path to exit using grid pathfinding
                if self.grid_pathfinder:
                    # Find nearest exit
                    nearest_exit = None
                    min_dist = float('inf')
                    for exit_id in self.env.exits:
                        exit_room = self.env.rooms[exit_id]
                        dist = abs(exit_room.x - agent.x) + abs(exit_room.y - agent.y)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_exit = exit_id
                    
                    if nearest_exit:
                        exit_room = self.env.rooms[nearest_exit]
                        grid_path = self.grid_pathfinder.find_path(
                            agent.x, agent.y, exit_room.x, exit_room.y,
                            avoid_danger=True, danger_threshold=0.8
                        )
                        if grid_path:
                            agent.target_room = nearest_exit
                            agent.waypoints = grid_path
                            agent.current_waypoint = 0
                            agent.state = AgentState.DRAGGING
                else:
                    # Fallback
                    exit_id, path = self.decision_engine.get_path_to_exit(agent.current_room)
                    if exit_id and path:
                        agent.start_rescuing(exit_id, path)
    
    def _process_dragging(self, agent: Agent):
        """Process agent dragging evacuee to exit"""
        # Similar to movement but with slower speed
        self._process_movement(agent)
    
    def _process_queued(self, agent: Agent):
        """Process agent waiting in queue"""
        # Waiting is passive - queue is processed when stair released
        pass
    
    def _check_completion(self):
        """Check if simulation should end"""
        # All evacuees rescued - SUCCESS!
        remaining_evac = self.env.get_remaining_evacuees()
        if remaining_evac == 0:
            self.complete = True
            self.running = False
            self.log_event(EventType.SIMULATION_END, None, None,
                         {'reason': 'all_rescued', 'time': self.time})
            return
        
        # All agents dead - FAILURE!
        all_dead = all(a.is_dead for a in self.agent_manager.agents)
        if all_dead:
            self.complete = True
            self.running = False
            self.log_event(EventType.SIMULATION_END, None, None,
                         {'reason': 'all_agents_dead', 'time': self.time})
            return
        
        # Time cap reached (very high limit)
        if self.time >= self.time_cap:
            self.complete = True
            self.running = False
            self.log_event(EventType.SIMULATION_END, None, None,
                         {'reason': 'time_limit', 'time': self.time})
    
    def run(self, max_ticks: Optional[int] = None):
        """
        Run simulation to completion
        
        Args:
            max_ticks: Maximum ticks to run (None = use time_cap)
        """
        self.running = True
        
        if max_ticks is None:
            max_ticks = int(self.time_cap / self.dt) + 1
        
        while self.running and self.tick < max_ticks:
            self.step()
        
        return self.get_results()
    
    def get_results(self) -> dict:
        """Get simulation results and metrics"""
        total_evac = self.env.get_total_evacuees()
        rescued = total_evac - self.env.get_remaining_evacuees()
        
        total_rooms = len([r for r in self.env.rooms.values() 
                          if not r.is_exit and not r.is_stair])
        cleared_rooms = len([r for r in self.env.rooms.values() 
                            if r.cleared])
        
        # Calculate SUCCESS RATE using CORRECT formula:
        # SR = (Survivors × Avg_Priority) / (Time × Responders)
        num_agents = self.params.get('agents', {}).get('count', 2)
        
        # Get average rescue priority from events
        rescue_events = [e for e in self.events if e.event_type == EventType.EVACUEE_RESCUED]
        if rescue_events:
            priorities = [e.data.get('priority', 100.0) for e in rescue_events]
            avg_priority = sum(priorities) / len(priorities)
        else:
            avg_priority = 100.0  # Default baseline
        
        # SUCCESS RATE formula
        if self.time > 0 and num_agents > 0:
            success_score = (rescued * avg_priority) / (self.time * num_agents)
        else:
            success_score = 0.0
        
        # Legacy metrics
        percent_rescued = rescued / total_evac if total_evac > 0 else 1.0
        percent_cleared = cleared_rooms / total_rooms if total_rooms > 0 else 1.0
        
        return {
            'time': self.time,
            'ticks': self.tick,
            'total_evacuees': total_evac,
            'evacuees_rescued': rescued,
            'percent_rescued': percent_rescued * 100,
            'total_rooms': total_rooms,
            'rooms_cleared': cleared_rooms,
            'percent_cleared': percent_cleared * 100,
            'success_score': success_score,
            'avg_priority': avg_priority,  # For displaying formula
            'num_responders': num_agents,
            'avg_hazard_exposure': self.agent_manager.get_average_hazard_exposure(),
            'max_hazard': self.env.hazard_system.get_max_hazard(),
            'agents': self.agent_manager.get_all_stats()
        }
    
    def reset(self):
        """Reset simulation to initial state"""
        self.tick = 0
        self.time = 0.0
        self.running = False
        self.complete = False
        self.events.clear()
        
        # Reset environment
        for room in self.env.rooms.values():
            room.cleared = False
            room.hazard = 0.0
            room.evacuees_remaining = room.evacuee_count
            room.discovered_evacuees = False
        
        # Recreate agents
        self.agent_manager = AgentManager(self.env, self.params.get('agents', {}))

