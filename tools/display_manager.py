from typing import Dict, List, Optional
import Quartz
from AppKit import NSScreen
import logging


logger = logging.getLogger(__name__)


class DisplayManager:
    """Native macOS display management"""
    
    def __init__(self):
        self.main_display = Quartz.CGMainDisplayID()
        
    def get_displays(self) -> List[Dict]:
        """Get all connected displays"""
        try:
            displays = []
            for screen in NSScreen.screens():
                frame = screen.frame()
                display_id = Quartz.CGDisplayGetDisplayID(screen)
                
                displays.append({
                    'id': display_id,
                    'width': frame.size.width,
                    'height': frame.size.height,
                    'x': frame.origin.x,
                    'y': frame.origin.y,
                    'is_main': display_id == self.main_display,
                    'is_retina': screen.backingScaleFactor() > 1.0,
                    'refresh_rate': self._get_refresh_rate(display_id)
                })
            return displays
        except Exception as e:
            logger.error(f"Failed to get displays: {e}")
            return []
            
    def set_display_mode(
        self,
        display_id: int,
        width: int,
        height: int,
        refresh_rate: Optional[float] = None
    ) -> bool:
        """Set display resolution and refresh rate"""
        try:
            # Get available modes
            modes = Quartz.CGDisplayCopyAllDisplayModes(display_id, None)
            
            # Find matching mode
            for mode in modes:
                mode_width = Quartz.CGDisplayModeGetWidth(mode)
                mode_height = Quartz.CGDisplayModeGetHeight(mode)
                mode_refresh = Quartz.CGDisplayModeGetRefreshRate(mode)
                
                if (mode_width == width and 
                    mode_height == height and
                    (refresh_rate is None or mode_refresh == refresh_rate)):
                    # Set display mode
                    Quartz.CGDisplaySetDisplayMode(display_id, mode, None)
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Failed to set display mode: {e}")
            return False
            
    def set_brightness(self, display_id: int, brightness: float) -> bool:
        """Set display brightness (0.0 to 1.0)"""
        try:
            return Quartz.CGDisplaySetBrightness(display_id, brightness)
        except Exception as e:
            logger.error(f"Failed to set brightness: {e}")
            return False
            
    def get_brightness(self, display_id: int) -> Optional[float]:
        """Get display brightness"""
        try:
            return Quartz.CGDisplayGetBrightness(display_id)
        except Exception as e:
            logger.error(f"Failed to get brightness: {e}")
            return None
            
    def _get_refresh_rate(self, display_id: int) -> float:
        """Get display refresh rate"""
        try:
            mode = Quartz.CGDisplayCopyDisplayMode(display_id)
            return Quartz.CGDisplayModeGetRefreshRate(mode)
        except Exception:
            return 0.0 