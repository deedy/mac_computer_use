from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import asyncio
import subprocess
import logging
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Configuration for different agent types"""
    name: str
    model: str
    role: str
    tools: List[str]
    memory_limit: Optional[int] = None
    priority: int = 1
    auto_restart: bool = True

class AgentManager:
    """Manages multiple agents across different terminals"""
    
    def __init__(self):
        self.agents: Dict[str, AgentConfig] = {}
        self.active_processes: Dict[str, subprocess.Popen] = {}
        
    async def create_agent(self, config: AgentConfig) -> str:
        """Create a new agent with specified configuration"""
        try:
            agent_id = f"{config.name}_{len(self.agents)}"
            self.agents[agent_id] = config
            
            # Create agent process
            await self.deploy_agent(agent_id)
            
            return agent_id
            
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            raise
            
    async def deploy_agent(self, agent_id: str):
        """Deploy agent in new terminal window"""
        try:
            config = self.agents[agent_id]
            
            # Create agent script
            script_path = self._create_agent_script(agent_id, config)
            
            # Launch in new terminal
            if os.name == 'posix':  # macOS/Linux
                process = subprocess.Popen([
                    'osascript',
                    '-e',
                    f'''
                    tell application "Terminal"
                        do script "python {script_path} --agent-id {agent_id}"
                    end tell
                    '''
                ])
            else:  # Windows
                process = subprocess.Popen([
                    'start',
                    'cmd',
                    '/k',
                    f'python {script_path} --agent-id {agent_id}'
                ], shell=True)
                
            self.active_processes[agent_id] = process
            
        except Exception as e:
            logger.error(f"Failed to deploy agent: {e}")
            raise
            
    def _create_agent_script(self, agent_id: str, config: AgentConfig) -> Path:
        """Create script file for agent"""
        script_dir = Path("agents")
        script_dir.mkdir(exist_ok=True)
        
        script_path = script_dir / f"{agent_id}.py"
        
        script_content = f"""
import asyncio
import sys
from mac_computer_use.tools.model_manager import ModelManager
from mac_computer_use.tools.tool_integration import ToolIntegrationManager

async def main():
    # Initialize agent
    model_manager = ModelManager()
    tool_manager = ToolIntegrationManager()
    
    # Load model
    await model_manager.load_model("{config.model}")
    
    # Get available tools
    tools = {{
        name: tool_manager.tools[name]
        for name in {config.tools}
    }}
    
    while True:
        try:
            # Get next task
            task = await get_next_task()
            
            # Process task
            response = await model_manager.generate(
                prompt=task["prompt"],
                tools=tools,
                temperature=0.7
            )
            
            # Send result
            await send_result(response)
            
        except Exception as e:
            print(f"Error: {{e}}")
            if not {config.auto_restart}:
                break
                
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
"""
        
        script_path.write_text(script_content)
        return script_path 