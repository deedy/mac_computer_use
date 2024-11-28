import asyncio
import base64
import os
import shlex
import pyautogui
import keyboard
from enum import StrEnum
from pathlib import Path
from typing import Literal, TypedDict, Optional, Dict, Any
from uuid import uuid4
from loguru import logger

from .base_tool import BaseTool, ToolResult
from .run import run
from .accessibility_integration import AccessibilityIntegration
from .activity_monitor import ActivityMonitor
from .sidecar import SidecarManager
from .cursor_integration import CursorIntegration
from .config_manager import ConfigManager
from .performance_monitor import PerformanceMonitor
from .cache_manager import CacheManager

OUTPUT_DIR = "/tmp/outputs"

TYPING_DELAY_MS = 12
TYPING_GROUP_SIZE = 50

Action = Literal[
    "key",
    "type",
    "mouse_move", 
    "left_click",
    "left_click_drag",
    "right_click",
    "middle_click",
    "double_click",
    "screenshot",
    "cursor_position",
    "open_app",  # Enhanced action
    "get_window_info",  # Enhanced action
    "monitor_activity",  # Enhanced action
    "sidecar_list",  # List available iPads
    "sidecar_connect",  # Connect to iPad
    "sidecar_configure",  # Configure Sidecar display
]


class Resolution(TypedDict):
    width: int
    height: int


# sizes above XGA/WXGA are not recommended
MAX_SCALING_TARGETS: dict[str, Resolution] = {
    "XGA": Resolution(width=1024, height=768),  # 4:3
    "WXGA": Resolution(width=1280, height=800),  # 16:10
    "FWXGA": Resolution(width=1366, height=768),  # ~16:9
}
SCALE_DESTINATION = MAX_SCALING_TARGETS["FWXGA"]


class ScalingSource(StrEnum):
    COMPUTER = "computer"
    API = "api"


class ComputerTool(BaseTool):
    """Enhanced tool for native macOS computer control"""

    def __init__(self):
        super().__init__()
        self.width, self.height = pyautogui.size()
        self.display_num = None  # macOS doesn't use X11 display numbers
        self.accessibility = AccessibilityIntegration()
        self.activity_monitor = ActivityMonitor()
        self.sidecar = SidecarManager()
        self.cursor = CursorIntegration()
        self.config = ConfigManager()
        self.performance = PerformanceMonitor()
        self.cache = CacheManager()
        
        # Configure from settings
        if self.config.config.cache_enabled:
            self._setup_caching()
            
    def _setup_caching(self):
        """Setup caching configuration"""
        # Configure cache settings
        pass
        
    async def execute(self, command: str, **kwargs) -> ToolResult:
        """Execute computer control actions"""
        try:
            # Parse command into action and parameters
            parts = command.split()
            action = parts[0].lower()
            
            if action == "open":
                app_name = " ".join(parts[1:])
                return await self._open_application(app_name)
                
            if action == "screenshot":
                return await self.screenshot()
                
            if action == "click":
                x = int(parts[1])
                y = int(parts[2])
                return await self._handle_mouse_movement("left_click", (x, y))
                
            if action == "type":
                text = " ".join(parts[1:])
                return await self._handle_keyboard_input("type", text)
                
            if action == "press":
                key = parts[1]
                return await self._handle_keyboard_input("key", key)
                
            raise ValueError(f"Invalid action: {action}")
            
        except Exception as e:
            logger.error(f"Failed to execute action: {e}")
            return ToolResult(success=False, error=str(e))

    async def _handle_mouse_movement(
        self, action: Action, coordinate: tuple[int, int] | None
    ) -> ToolResult:
        """Handle mouse movement actions"""
        try:
            if coordinate is None:
                raise ValueError(f"coordinate is required for {action}")
                
            x, y = coordinate
            pyautogui.moveTo(x, y)
            
            if action == "left_click":
                pyautogui.click()
                
            return ToolResult(success=True)
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _handle_keyboard_input(
        self, action: Action, text: str | None
    ) -> ToolResult:
        """Handle keyboard input actions"""
        try:
            if text is None:
                raise ValueError(f"text is required for {action}")
                
            if action == "key":
                keyboard.press_and_release(text)
            else:
                keyboard.write(text)
                
            return ToolResult(success=True)
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _open_application(self, app_name: str) -> ToolResult:
        """Open macOS application"""
        try:
            # Clean up app name
            app_name = app_name.strip()
            
            # Try to open the app using AppleScript first
            script = f'tell application "{app_name}" to activate'
            proc = await asyncio.create_subprocess_shell(
                f'osascript -e \'{script}\'',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                # Fallback to open command
                proc = await asyncio.create_subprocess_shell(
                    f'open -a "{app_name}"',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                
            if proc.returncode != 0:
                return ToolResult(
                    success=False,
                    error=f"Failed to open {app_name}: {stderr.decode()}"
                )
                
            # Wait for app to launch
            await asyncio.sleep(2)
            
            return ToolResult(
                success=True,
                output=f"Opened {app_name}"
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Error opening {app_name}: {str(e)}"
            )

    async def screenshot(self) -> ToolResult:
        """Take a screenshot"""
        try:
            # Create output directory if it doesn't exist
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            
            # Generate unique filename
            filename = f"{OUTPUT_DIR}/screenshot_{uuid4().hex}.png"
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            
            # Convert to base64
            with open(filename, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
                
            # Cleanup
            os.remove(filename)
            
            return ToolResult(
                success=True,
                base64_image=image_data
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Screenshot failed: {str(e)}"
            )

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if hasattr(self, "activity_monitor"):
                await self.activity_monitor.cleanup()
            if hasattr(self, "sidecar"):
                await self.sidecar.cleanup()
            if hasattr(self, "cursor"):
                await self.cursor.cleanup()
        except Exception as e:
            logger.error(f"Error cleaning up ComputerTool: {e}")
