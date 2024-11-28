from typing import Dict
from AppKit import NSWorkspace, NSPoint
import logging


logger = logging.getLogger(__name__)


class AccessibilityIntegration:
    """Native macOS accessibility support for UI interaction"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
    
    async def get_element_info(self, coordinate: tuple[int, int]) -> Dict:
        """Get accessibility information for element at coordinates"""
        try:
            # Convert coordinate to NSPoint and use it to get element
            point = NSPoint(coordinate[0], coordinate[1])
            app = self.workspace.frontmostApplication()
            
            # Get element at point if app exists
            if app:
                element = app.elementAtPoint_(point)
                if element:
                    return {
                        'role': element.role(),
                        'title': element.title(),
                        'description': element.description(),
                        'value': element.value(),
                        'position': coordinate,
                        'size': element.size()
                    }
                return {
                    'role': 'application',
                    'title': app.localizedName(),
                    'description': '',
                    'value': None,
                    'position': coordinate,
                    'size': (0, 0)
                }
        except Exception as e:
            logger.error(f"Error getting accessibility info: {e}")
            
        return {
            'role': 'unknown',
            'title': '',
            'description': '',
            'value': None,
            'position': coordinate,
            'size': (0, 0)
        }
        
    async def get_active_window_info(self) -> Dict:
        """Get information about active window"""
        try:
            app = self.workspace.frontmostApplication()
            if app:
                windows = app.windows()
                title = windows[0].title() if windows else ''
                return {
                    'app_name': app.localizedName(),
                    'window_title': title,
                    'is_active': True,
                    'position': (0, 0),
                    'size': (0, 0)
                }
        except Exception as e:
            logger.error(f"Error getting window info: {e}")
            
        return {
            'app_name': '',
            'window_title': '',
            'is_active': False,
            'position': (0, 0),
            'size': (0, 0)
        }