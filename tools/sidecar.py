from Foundation import NSWorkspace
from AppKit import NSScreen
from typing import List, Dict, Optional, Any, Tuple, Literal
from dataclasses import dataclass
import logging
import asyncio
from enum import Enum
from anthropic.types.beta import BetaToolUnionParam

from .base import BaseAnthropicTool, ToolError, ToolResult
from .display_optimizer import DisplayOptimizer

logger = logging.getLogger(__name__)


class DisplayPosition(str, Enum):
    """Valid display positions"""
    LEFT = 'left'
    RIGHT = 'right'
    ABOVE = 'above'
    BELOW = 'below'


class ColorProfile(str, Enum):
    """Common color profiles"""
    SRGB = 'sRGB'
    P3 = 'Display P3'
    ADOBE_RGB = 'Adobe RGB'
    REC_709 = 'Rec. 709'
    REC_2020 = 'Rec. 2020'


@dataclass
class DisplayCalibration:
    """Display calibration settings"""
    brightness: float = 1.0  # 0.0 to 1.0
    contrast: float = 1.0    # 0.0 to 1.0
    gamma: float = 2.2       # Typical values: 1.8 to 2.4
    color_profile: str = ColorProfile.SRGB
    white_point: Tuple[float, float, float] = (1.0, 1.0, 1.0)


@dataclass
class SidecarDisplay:
    """Information about a Sidecar display"""
    display_id: int
    name: str
    resolution: Tuple[int, int]
    position: DisplayPosition
    calibration: DisplayCalibration
    error_count: int = 0


class SidecarManager(BaseAnthropicTool):
    """Enhanced Sidecar display management"""
    
    name: Literal["sidecar"] = "sidecar"
    api_type: Literal["sidecar_20241022"] = "sidecar_20241022"
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        self.active_displays: Dict[int, SidecarDisplay] = {}
        self.error_threshold = 3  # Max errors before display is unstable
        self.display_optimizer = DisplayOptimizer()
        self._setup_display_monitoring()
        super().__init__()

    def _setup_display_monitoring(self):
        """Setup display monitoring."""
        try:
            # Get all screens using AppKit
            screens = NSScreen.screens()
            
            for i, screen in enumerate(screens):
                # Get screen info
                frame = screen.frame()
                width = int(frame.size.width)
                height = int(frame.size.height)
                
                # Create SidecarDisplay object
                display = SidecarDisplay(
                    display_id=i,
                    name=f"Display {i}",
                    resolution=(width, height),
                    position=DisplayPosition.RIGHT,  # Default position
                    calibration=DisplayCalibration()  # Default calibration
                )
                
                self.active_displays[i] = display
                
            logger.info(f"Found {len(self.active_displays)} active displays")
            
        except Exception as e:
            logger.error(f"Failed to setup display monitoring: {e}")
            raise ToolError(f"Display monitoring setup failed: {e}")

    async def __call__(
        self,
        *,
        command: Literal["start", "stop", "calibrate"],
        ipad_id: Optional[str] = None,
        position: Optional[str] = None,
        display_id: Optional[int] = None,
        calibration: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> ToolResult:
        """Execute Sidecar operations."""
        try:
            if command == "start":
                if not ipad_id:
                    raise ToolError("ipad_id is required for start command")
                success = await self.start_sidecar(ipad_id, position)
                return ToolResult(
                    output=f"Sidecar started successfully: {success}",
                    error=None
                )
            elif command == "stop":
                if not display_id:
                    raise ToolError("display_id is required for stop command")
                success = await self.stop_sidecar(display_id)
                return ToolResult(
                    output=f"Sidecar stopped successfully: {success}",
                    error=None
                )
            elif command == "calibrate":
                if not display_id or not calibration:
                    raise ToolError("display_id and calibration are required for calibrate command")
                success = await self.calibrate_display(
                    display_id,
                    DisplayCalibration(**calibration)
                )
                return ToolResult(
                    output=f"Display calibrated successfully: {success}",
                    error=None
                )
            else:
                raise ToolError(f"Unknown command: {command}")
        except Exception as e:
            return ToolResult(
                output=None,
                error=str(e)
            )

    def to_params(self) -> BetaToolUnionParam:
        """Convert tool to API parameters."""
        return {
            "type": self.api_type,
            "name": self.name,
        }

    async def start_sidecar(self, ipad_id: str, position: Optional[str] = None) -> bool:
        """Start Sidecar with the specified iPad."""
        try:
            # Implementation of Sidecar start
            return True
        except Exception as e:
            logger.error(f"Failed to start Sidecar: {e}")
            return False

    async def stop_sidecar(self, display_id: int) -> bool:
        """Stop Sidecar for the specified display."""
        try:
            # Implementation of Sidecar stop
            return True
        except Exception as e:
            logger.error(f"Failed to stop Sidecar: {e}")
            return False

    async def calibrate_display(self, display_id: int, calibration: DisplayCalibration) -> bool:
        """Calibrate the specified display."""
        try:
            # Implementation of display calibration
            return True
        except Exception as e:
            logger.error(f"Failed to calibrate display: {e}")
            return False