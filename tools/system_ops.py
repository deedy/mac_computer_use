"""System operations tool for Mac computer control."""

import os
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional
from .base import BaseTool, ToolResult
from .logging_config import logger

class SystemOperationsTool(BaseTool):
    """Tool for system operations like screenshots, etc."""
    
    def __init__(self):
        """Initialize system operations tool."""
        super().__init__()
        self.screenshots_dir = os.path.expanduser("~/Desktop/Screenshots")
        if not os.path.exists(self.screenshots_dir):
            os.makedirs(self.screenshots_dir)
    
    async def execute(self, command: str, context: Dict[str, Any] = None) -> ToolResult:
        """Execute system operation command."""
        try:
            if "screenshot" in command.lower():
                return await self.take_screenshot()
            else:
                return {
                    "success": False,
                    "data": None,
                    "error": "Unsupported system operation",
                    "metadata": {}
                }
        except Exception as e:
            logger.error(f"System operation failed: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e),
                "metadata": {"error_type": "system_operation_error"}
            }
    
    async def take_screenshot(self) -> ToolResult:
        """Take a screenshot of the entire screen."""
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Use screencapture command (built into macOS)
            result = subprocess.run(
                ["screencapture", "-x", filepath],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "data": f"Screenshot saved to {filepath}",
                    "error": None,
                    "metadata": {"filepath": filepath}
                }
            else:
                return {
                    "success": False,
                    "data": None,
                    "error": f"Screenshot failed: {result.stderr}",
                    "metadata": {}
                }
                
        except subprocess.CalledProcessError as e:
            error_msg = f"Screenshot command failed: {e.stderr}"
            logger.error(error_msg)
            return {
                "success": False,
                "data": None,
                "error": error_msg,
                "metadata": {}
            }
        except Exception as e:
            error_msg = f"Screenshot failed: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "data": None,
                "error": error_msg,
                "metadata": {}
            } 