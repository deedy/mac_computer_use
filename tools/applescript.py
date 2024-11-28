from typing import Optional, Dict
from AppKit import NSAppleScript, NSAppleEventDescriptor
import logging


logger = logging.getLogger(__name__)


class AppleScriptExecutor:
    """Execute AppleScript commands natively"""
    
    def __init__(self):
        self._last_error = None
        
    async def execute(self, script: str) -> Dict:
        """Execute an AppleScript command"""
        try:
            # Create and execute script
            script_obj = NSAppleScript.alloc().initWithSource_(script)
            result, error = script_obj.executeAndReturnError_(None)
            
            if error:
                self._last_error = error
                logger.error(f"AppleScript error: {error}")
                return {
                    'success': False,
                    'error': str(error),
                    'result': None
                }
                
            # Parse result if available
            if result:
                return {
                    'success': True,
                    'error': None,
                    'result': self._parse_result(result)
                }
                
            return {
                'success': True,
                'error': None,
                'result': None
            }
            
        except Exception as e:
            logger.error(f"Failed to execute AppleScript: {e}")
            return {
                'success': False,
                'error': str(e),
                'result': None
            }
            
    def _parse_result(
        self, 
        result: NSAppleEventDescriptor
    ) -> Optional[str]:
        """Parse AppleScript result"""
        try:
            if result.stringValue():
                return result.stringValue()
            return None
        except Exception:
            return None
            
    def get_last_error(self) -> Optional[str]:
        """Get the last error that occurred"""
        if self._last_error:
            return str(self._last_error)
        return None 