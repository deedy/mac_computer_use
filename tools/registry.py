from typing import Dict, Type, List
import logging
from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class ToolRegistry:
    """Central registry for tool management"""
    
    _instance = None
    _tools: Dict[str, BaseTool] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
        return cls._instance
        
    def register(self, tool: BaseTool):
        """Register a new tool instance"""
        tool_name = tool.__class__.__name__
        if tool_name in self._tools:
            logger.warning(f"Tool {tool_name} already registered, overwriting")
        self._tools[tool_name] = tool
        logger.info(f"Registered tool: {tool_name}")
        
    def get_tool(self, name: str) -> BaseTool:
        """Get tool instance by name"""
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")
        return self._tools[name]
        
    def list_tools(self) -> List[str]:
        """List all registered tools"""
        return list(self._tools.keys())
        
    def unregister(self, name: str):
        """Unregister a tool"""
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}") 