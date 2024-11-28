"""Collection classes for managing multiple tools."""

import asyncio
from typing import List, Optional, Dict
import logging

from .base_tool import BaseTool, ToolResult
from .registry import ToolRegistry
from .error_handler import ErrorHandler
from .config_manager import ConfigManager
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class ToolCollection:
    """Enhanced tool collection with improved management"""

    def __init__(self):
        self.registry = ToolRegistry()
        self.error_handler = ErrorHandler()
        self.config = ConfigManager()
        self.cache = CacheManager()

    async def initialize(self):
        """Initialize tool collection"""
        try:
            # Initialize each registered tool
            for tool_name in self.registry.list_tools():
                tool = self.registry.get_tool(tool_name)
                if await tool.validate():
                    logger.info(f"Initialized tool: {tool_name}")
                else:
                    logger.warning(f"Tool validation failed: {tool_name}")
                    
        except Exception as e:
            logger.error(f"Tool collection initialization failed: {e}")
            raise
            
    async def execute(self, 
                     tool_name: str,
                     command: str,
                     **kwargs) -> ToolResult:
        """Execute tool command with error handling and caching"""
        try:
            tool = self.registry.get_tool(tool_name)
            
            # Check cache if enabled
            if self.config.cache_enabled:
                cache_key = f"{tool_name}:{command}:{str(kwargs)}"
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    return cached_result
                    
            # Execute tool
            result = await tool.execute(command, **kwargs)
            
            # Cache successful result
            if result.success and self.config.cache_enabled:
                await self.cache.set(cache_key, result)
                
            return result
            
        except Exception as e:
            # Handle error
            context = self.error_handler.handle_error(
                e, tool_name, command, **kwargs
            )
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"error_context": context}
            )
            
    async def cleanup(self):
        """Cleanup all tools"""
        for tool_name in self.registry.list_tools():
            tool = self.registry.get_tool(tool_name)
            await tool.cleanup()
