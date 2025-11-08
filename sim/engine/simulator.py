"""Main simulation engine with tick loop"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Callable
import numpy as np

from ..env.environment import Environment
from ..agents.agent_manager import AgentManager
from ..agents.agent import Agent, AgentState
from ..policy.decision_engine import DecisionEngine


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
        
        # 2. Process each agent
        for agent in self.agent_manager.agents:
            self._process_agent(agent)
        
        # 3. Check completion
        self._check_completion()
        
        # 4. Increment time
        self.tick += 1
        self.time += self.dt
    
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
        """Assign next target room to idle agent"""
        # Select best room
        room_score = self.decision_engine.select_next_room(agent)
        
        if room_score:
            agent.set_target(room_score.room_id, room_score.path)
            self.log_event(EventType.AGENT_MOVE, agent.id, agent.current_room,
                         {'target': room_score.room_id, 'score': room_score.score})
    
    def _process_movement(self, agent: Agent):
        """Process agent movement along path"""
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
        
        # Move to next room
        next_room = self.env.rooms[next_room_id]
        agent.update_position(next_room.x, next_room.y, next_room.floor, next_room_id)
        agent.advance_path()
        
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
        
        # Check if this is exit delivery
        if target_room.is_exit and agent.carrying_evacuee:
            # Actually remove evacuee from source room
            if agent.evacuee_source_room and agent.evacuee_source_room in self.env.rooms:
                source_room = self.env.rooms[agent.evacuee_source_room]
                source_room.rescue_evacuee()
            
            # Log rescue
            self.log_event(EventType.EVACUEE_RESCUED, agent.id, agent.target_room,
                         {'source_room': agent.evacuee_source_room})
            
            # Check if more evacuees need rescuing from source room
            source_room_id = agent.evacuee_source_room
            agent.complete_rescue()
            
            if source_room_id and source_room_id in self.env.rooms:
                source_room = self.env.rooms[source_room_id]
                if source_room.evacuees_remaining > 0:
                    # Go back for more evacuees
                    exit_id, path = self.decision_engine.get_path_to_exit(source_room_id)
                    if exit_id and path:
                        # Get path to source room first
                        path_to_source = self.env.get_shortest_path(agent.current_room, source_room_id)
                        if path_to_source:
                            agent.evacuee_source_room = source_room_id
                            agent.set_target(source_room_id, path_to_source)
                            agent.state = AgentState.MOVING
                            # Will pick up evacuee when arriving at source
        
        # Check if arriving at room with evacuees to pickup (returning for more)
        elif (target_room.cleared and target_room.evacuees_remaining > 0 and 
              not agent.carrying_evacuee and agent.evacuee_source_room == agent.target_room):
            # Pick up evacuee and head to exit
            exit_id, path = self.decision_engine.get_path_to_exit(agent.current_room)
            if exit_id and path:
                agent.start_rescuing(exit_id, path)
        
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
                # Found evacuees - start rescue
                self.log_event(EventType.EVACUEE_FOUND, agent.id, agent.current_room,
                             {'count': evac_count})
                
                # Get path to exit
                exit_id, path = self.decision_engine.get_path_to_exit(agent.current_room)
                if exit_id and path:
                    agent.evacuee_source_room = agent.current_room
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
        # Time cap reached
        if self.time >= self.time_cap:
            self.complete = True
            self.running = False
            self.log_event(EventType.SIMULATION_END, None, None,
                         {'reason': 'time_cap', 'time': self.time})
            return
        
        # All rooms cleared and no evacuees remaining
        uncleared = self.env.get_uncleared_rooms()
        remaining_evac = self.env.get_remaining_evacuees()
        
        # Check if all agents are idle and no work left
        all_idle = all(a.state == AgentState.IDLE for a in self.agent_manager.agents)
        
        if not uncleared and remaining_evac == 0 and all_idle:
            self.complete = True
            self.running = False
            self.log_event(EventType.SIMULATION_END, None, None,
                         {'reason': 'complete', 'time': self.time})
    
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
        
        # Calculate success score S
        percent_rescued = rescued / total_evac if total_evac > 0 else 1.0
        percent_cleared = cleared_rooms / total_rooms if total_rooms > 0 else 1.0
        time_factor = 1.0 - (self.time / self.time_cap)  # Better if faster
        
        success_score = (percent_rescued * 0.5 + percent_cleared * 0.3 + 
                        time_factor * 0.2)
        
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

