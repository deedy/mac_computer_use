from typing import Dict, List, Optional, Tuple
import Quartz
from AppKit import NSWorkspace, NSScreen, NSWindow
import logging
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class WindowInfo:
    """Information about a window"""
    id: int
    pid: int
    app_name: str
    title: str
    frame: Tuple[int, int, int, int]  # x, y, width, height
    is_minimized: bool
    is_on_screen: bool
    alpha: float
    level: int
    workspace: Optional[int] = None


class WindowManager:
    """Native macOS window management"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        
    def get_window_list(self) -> List[WindowInfo]:
        """Get list of all windows"""
        try:
            window_list = []
            window_info = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionOnScreenOnly | 
                Quartz.kCGWindowListExcludeDesktopElements,
                Quartz.kCGNullWindowID
            )
            
            for window in window_info:
                try:
                    info = WindowInfo(
                        id=window.get(Quartz.kCGWindowNumber, 0),
                        pid=window.get(Quartz.kCGWindowOwnerPID, 0),
                        app_name=window.get(Quartz.kCGWindowOwnerName, ""),
                        title=window.get(Quartz.kCGWindowName, ""),
                        frame=self._parse_frame(
                            window.get(Quartz.kCGWindowBounds)
                        ),
                        is_minimized=window.get(
                            Quartz.kCGWindowIsOnscreen,
                            False
                        ),
                        is_on_screen=window.get(
                            Quartz.kCGWindowIsOnscreen,
                            False
                        ),
                        alpha=window.get(Quartz.kCGWindowAlpha, 1.0),
                        level=window.get(Quartz.kCGWindowLayer, 0),
                        workspace=self._get_window_workspace(
                            window.get(Quartz.kCGWindowNumber, 0)
                        )
                    )
                    window_list.append(info)
                except Exception as e:
                    logger.error(f"Failed to parse window info: {e}")
                    continue
                    
            return window_list
            
        except Exception as e:
            logger.error(f"Failed to get window list: {e}")
            return []
            
    def focus_window(self, window_id: int) -> bool:
        """Focus a specific window"""
        try:
            window = self._get_window_by_id(window_id)
            if window:
                window.makeKeyAndOrderFront_(None)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to focus window: {e}")
            return False
            
    def set_window_frame(
        self,
        window_id: int,
        x: int,
        y: int,
        width: int,
        height: int
    ) -> bool:
        """Set window position and size"""
        try:
            window = self._get_window_by_id(window_id)
            if window:
                frame = window.frame()
                frame.origin.x = x
                frame.origin.y = y
                frame.size.width = width
                frame.size.height = height
                window.setFrame_display_(frame, True)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to set window frame: {e}")
            return False
            
    def _parse_frame(self, bounds_dict: Dict) -> Tuple[int, int, int, int]:
        """Parse CGRect bounds dictionary"""
        try:
            return (
                int(bounds_dict["X"]),
                int(bounds_dict["Y"]),
                int(bounds_dict["Width"]),
                int(bounds_dict["Height"])
            )
        except (KeyError, TypeError):
            return (0, 0, 0, 0)
            
    def _get_window_workspace(self, window_id: int) -> Optional[int]:
        """Get workspace number for window"""
        try:
            for i, workspace in enumerate(
                NSWorkspace.sharedWorkspace().activeWorkspace()
            ):
                if window_id in workspace.windowIDs():
                    return i
            return None
        except Exception:
            return None
            
    def _get_window_by_id(self, window_id: int) -> Optional[NSWindow]:
        """Get NSWindow object by ID"""
        try:
            for window in NSWindow.windowNumbersWithOptions_(0):
                if window.windowNumber() == window_id:
                    return window
            return None
        except Exception:
            return None