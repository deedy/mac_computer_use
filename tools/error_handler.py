from typing import Optional, Dict, Any, List
import traceback
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ErrorContext:
    """Error context information"""
    timestamp: datetime
    tool_name: str
    command: str
    args: Dict[str, Any]
    traceback: str
    
class ErrorHandler:
    """Centralized error handling"""
    
    def __init__(self):
        self.error_history: List[ErrorContext] = []
        
    def handle_error(self, 
                    error: Exception,
                    tool_name: str,
                    command: str,
                    **kwargs) -> ErrorContext:
        """Handle and log tool errors"""
        context = ErrorContext(
            timestamp=datetime.now(),
            tool_name=tool_name,
            command=command,
            args=kwargs,
            traceback=traceback.format_exc()
        )
        
        # Log error
        logger.error(
            f"Tool error in {tool_name}\n"
            f"Command: {command}\n"
            f"Args: {kwargs}\n"
            f"Error: {str(error)}\n"
            f"Traceback:\n{context.traceback}"
        )
        
        # Store in history
        self.error_history.append(context)
        return context
        
    def get_error_history(self, 
                         tool_name: Optional[str] = None,
                         limit: Optional[int] = None) -> List[ErrorContext]:
        """Get error history with optional filtering"""
        history = self.error_history
        
        if tool_name:
            history = [e for e in history if e.tool_name == tool_name]
            
        if limit:
            history = history[-limit:]
            
        return history 