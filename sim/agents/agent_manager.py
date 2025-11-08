"""Agent manager for coordinating multiple agents"""

from typing import List, Dict, Optional
from .agent import Agent, AgentState
from ..env.environment import Environment


class AgentManager:
    """Manages all firefighter agents"""
    
    def __init__(self, environment: Environment, params: dict):
        """
        Initialize agent manager
        
        Args:
            environment: Building environment
            params: Agent parameters
        """
        self.env = environment
        self.params = params
        self.agents: List[Agent] = []
        
        # Stair queue management
        self.stair_queues: Dict[str, List[int]] = {}  # stair_id -> agent_ids waiting
        self.stair_occupancy: Dict[str, Optional[int]] = {}  # stair_id -> agent_id or None
        
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Create agents at starting positions"""
        num_agents = self.params.get('count', 2)
        starts = self.env.agent_starts
        
        # If not enough starts defined, use first exit
        if not starts and self.env.exits:
            exit_room = self.env.rooms[self.env.exits[0]]
            starts = [(exit_room.x, exit_room.y, exit_room.floor)]
        
        for i in range(num_agents):
            # Cycle through available starts
            if starts:
                x, y, floor = starts[i % len(starts)]
            else:
                # Default to origin
                x, y, floor = 0, 0, 0
            
            # Find room at this position
            room = self.env.get_room_at_position(x, y, floor)
            if room:
                current_room = room.id
            else:
                # Use first room on floor as fallback
                floor_rooms = self.env.floors.get(floor, [])
                current_room = floor_rooms[0] if floor_rooms else list(self.env.rooms.keys())[0]
                room = self.env.rooms[current_room]
                x, y = room.x, room.y
            
            agent = Agent(i, x, y, floor, current_room, self.params)
            self.agents.append(agent)
    
    def get_agent(self, agent_id: int) -> Optional[Agent]:
        """Get agent by ID"""
        if 0 <= agent_id < len(self.agents):
            return self.agents[agent_id]
        return None
    
    def get_idle_agents(self) -> List[Agent]:
        """Get all agents in IDLE state"""
        return [a for a in self.agents if a.state == AgentState.IDLE]
    
    def get_agents_on_floor(self, floor: int) -> List[Agent]:
        """Get all agents on a specific floor"""
        return [a for a in self.agents if a.floor == floor]
    
    def is_stair_available(self, stair_id: str, agent_id: int) -> bool:
        """Check if a stair is available for agent to use"""
        if stair_id not in self.stair_occupancy:
            self.stair_occupancy[stair_id] = None
        
        occupant = self.stair_occupancy[stair_id]
        return occupant is None or occupant == agent_id
    
    def occupy_stair(self, stair_id: str, agent_id: int):
        """Mark stair as occupied by agent"""
        self.stair_occupancy[stair_id] = agent_id
    
    def release_stair(self, stair_id: str):
        """Release stair occupancy"""
        self.stair_occupancy[stair_id] = None
        
        # Process queue
        if stair_id in self.stair_queues and self.stair_queues[stair_id]:
            next_agent_id = self.stair_queues[stair_id].pop(0)
            next_agent = self.get_agent(next_agent_id)
            if next_agent and next_agent.state == AgentState.QUEUED:
                next_agent.state = AgentState.MOVING
                self.occupy_stair(stair_id, next_agent_id)
    
    def enqueue_for_stair(self, stair_id: str, agent_id: int):
        """Add agent to stair queue"""
        if stair_id not in self.stair_queues:
            self.stair_queues[stair_id] = []
        
        if agent_id not in self.stair_queues[stair_id]:
            self.stair_queues[stair_id].append(agent_id)
        
        agent = self.get_agent(agent_id)
        if agent:
            agent.state = AgentState.QUEUED
    
    def get_total_rooms_cleared(self) -> int:
        """Get total rooms cleared by all agents"""
        return sum(a.rooms_cleared for a in self.agents)
    
    def get_total_evacuees_rescued(self) -> int:
        """Get total evacuees rescued by all agents"""
        return sum(a.evacuees_rescued for a in self.agents)
    
    def get_average_hazard_exposure(self) -> float:
        """Get average hazard exposure across all agents"""
        if not self.agents:
            return 0.0
        return sum(a.cumulative_hazard_exposure for a in self.agents) / len(self.agents)
    
    def get_all_stats(self) -> List[dict]:
        """Get statistics for all agents"""
        return [agent.get_stats() for agent in self.agents]
    
    def __repr__(self):
        return f"AgentManager(agents={len(self.agents)})"

