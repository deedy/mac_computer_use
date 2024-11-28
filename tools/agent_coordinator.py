from dataclasses import dataclass
from typing import Dict, List, Optional
import asyncio
import logging
from queue import PriorityQueue

logger = logging.getLogger(__name__)

@dataclass
class Task:
    """Task for agents to process"""
    priority: int
    prompt: str
    tools: List[str]
    agent_id: Optional[str] = None

class AgentCoordinator:
    """Coordinates tasks between multiple agents"""
    
    def __init__(self):
        self.task_queue = PriorityQueue()
        self.results: Dict[str, str] = {}
        self.agent_status: Dict[str, str] = {}
        
    async def submit_task(self, task: Task):
        """Submit task for processing"""
        try:
            # Add task to queue
            self.task_queue.put((task.priority, task))
            
            # Notify available agents
            await self._notify_agents()
            
        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            raise
            
    async def get_result(self, task_id: str) -> Optional[str]:
        """Get task result"""
        return self.results.get(task_id)
        
    async def _notify_agents(self):
        """Notify available agents of new tasks"""
        try:
            # Find available agents
            available_agents = [
                agent_id
                for agent_id, status in self.agent_status.items()
                if status == "idle"
            ]
            
            # Assign tasks to agents
            while not self.task_queue.empty() and available_agents:
                agent_id = available_agents.pop(0)
                _, task = self.task_queue.get()
                
                # Assign task
                task.agent_id = agent_id
                self.agent_status[agent_id] = "busy"
                
                # Start processing
                asyncio.create_task(self._process_task(task))
                
        except Exception as e:
            logger.error(f"Failed to notify agents: {e}")
            raise 