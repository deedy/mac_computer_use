from dataclasses import dataclass
from typing import Dict, List, Optional
import logging
import asyncio
from queue import PriorityQueue

logger = logging.getLogger(__name__)


@dataclass
class TaskMetadata:
    """Metadata for task routing"""
    task_type: str  # code/text/chat/math
    priority: int
    complexity: float  # 0.0 to 1.0
    requires_tools: List[str]
    timeout: Optional[float] = None


class OrchestratorAgent:
    """Agent for task routing and orchestration"""
    
    def __init__(self):
        self.task_queue = PriorityQueue()
        self.agent_capabilities = {}
        self.model_specialties = {
            "code": ["codellama-34b"],
            "chat": ["qwen-7b", "mistral-7b"],
            "math": ["phi-2"],
            "general": ["mistral-7b"]
        }
        
    async def route_task(self, prompt: str, metadata: TaskMetadata):
        """Route task to appropriate agent/model"""
        try:
            # Analyze task requirements
            task_type = metadata.task_type
            complexity = metadata.complexity
            
            # Select optimal model
            if complexity > 0.8:
                # Use more powerful models for complex tasks
                model = self.model_specialties[task_type][0]
            else:
                # Use faster/lighter models for simpler tasks
                model = self.model_specialties[task_type][-1]
                
            # Find available agent
            agent = await self._find_agent(
                task_type=task_type,
                required_tools=metadata.requires_tools
            )
            
            # Queue task
            self.task_queue.put(
                (metadata.priority, {
                    "prompt": prompt,
                    "model": model,
                    "agent": agent,
                    "metadata": metadata
                })
            )
            
        except Exception as e:
            logger.error(f"Task routing failed: {e}")
            raise
            
    async def _find_agent(self, task_type: str, required_tools: List[str]):
        """Find suitable agent for task"""
        available_agents = []
        
        for agent_id, capabilities in self.agent_capabilities.items():
            if task_type in capabilities["types"] and \
               all(tool in capabilities["tools"] for tool in required_tools):
                available_agents.append(agent_id)
                
        if not available_agents:
            raise ValueError(f"No suitable agent for {task_type}")
            
        return available_agents[0]  # Return first matching agent 