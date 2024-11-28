from dataclasses import dataclass
import logging
from typing import Dict, List, Set, Optional
import asyncio
import zmq.asyncio

logger = logging.getLogger(__name__)

@dataclass
class AgentCapability:
    """Capability metadata for an agent"""
    agent_id: str
    specialties: Set[str]
    current_load: float
    success_rate: float

class CollaborationAgent:
    """Coordinates collaboration between agents"""
    
    def __init__(self):
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        self.active_collaborations: Dict[str, List[str]] = {}
        self.context = zmq.asyncio.Context()
        
    async def register_agent(self, agent_id: str, capabilities: AgentCapability):
        """Register a new agent's capabilities"""
        self.agent_capabilities[agent_id] = capabilities
        
    async def form_team(self, task_requirements: Dict) -> List[str]:
        """Form optimal team for task"""
        try:
            needed_specialties = set(task_requirements["required_skills"])
            team = []
            
            # Find agents with required specialties
            for specialty in needed_specialties:
                best_agent = await self._find_best_agent(specialty)
                if best_agent:
                    team.append(best_agent)
                    
            if len(team) < len(needed_specialties):
                raise ValueError("Could not find agents for all required skills")
                
            # Register collaboration
            collab_id = f"collab_{len(self.active_collaborations)}"
            self.active_collaborations[collab_id] = team
            
            return team
            
        except Exception as e:
            logger.error(f"Team formation failed: {e}")
            raise
            
    async def _find_best_agent(self, specialty: str) -> Optional[str]:
        """Find best agent for a specialty"""
        candidates = [
            (agent_id, cap) 
            for agent_id, cap in self.agent_capabilities.items()
            if specialty in cap.specialties and cap.current_load < 0.8
        ]
        
        if not candidates:
            return None
            
        # Sort by success rate and load
        candidates.sort(key=lambda x: (x[1].success_rate, -x[1].current_load))
        return candidates[-1][0] 