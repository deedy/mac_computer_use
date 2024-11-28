from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ToolResult:
    """Standardized tool execution result"""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseTool(ABC):
    """Base class for all computer_use tools"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(self.name)
        
    @abstractmethod
    async def execute(self, command: str, **kwargs) -> ToolResult:
        """Execute tool command"""
        pass
        
    async def validate(self, **kwargs) -> bool:
        """Validate tool requirements and configuration"""
        return True
        
    async def cleanup(self):
        """Cleanup tool resources"""
        pass
        
    def _format_error(self, error: Exception) -> str:
        """Format error message with context"""
        return f"{self.name} error: {str(error)}" 