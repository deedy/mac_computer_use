from typing import Optional, Dict, Tuple, Callable
from AppKit import (
    NSEvent,
    NSEventMaskLeftMouseDown,
    NSEventMaskLeftMouseUp,
    NSEventMaskRightMouseDown,
    NSEventMaskRightMouseUp,
    NSEventMaskMouseMoved,
    NSPoint,
    NSScreen
)
import Quartz
import logging
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class MouseButton(str, Enum):
    """Mouse buttons"""
    LEFT = 'left'
    RIGHT = 'right'
    MIDDLE = 'middle'


@dataclass
class MouseEvent:
    """Mouse event information"""
    position: Tuple[int, int]
    button: Optional[MouseButton]
    is_pressed: bool
    timestamp: float
    modifiers: list[str] = None


class MouseManager:
    """Native macOS mouse management"""
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.monitoring = False
        self._setup_monitoring()
        
    def _setup_monitoring(self):
        """Setup mouse event monitoring"""
        mask = (
            NSEventMaskLeftMouseDown |
            NSEventMaskLeftMouseUp |
            NSEventMaskRightMouseDown |
            NSEventMaskRightMouseUp |
            NSEventMaskMouseMoved
        )
        NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            mask,
            self._handle_event
        )
        self.monitoring = True
        
    def move_mouse(self, x: int, y: int, smooth: bool = True):
        """Move mouse cursor"""
        try:
            if smooth:
                # Get current position
                pos = Quartz.CGEventGetLocation(
                    Quartz.CGEventCreate(None)
                )
                
                # Calculate steps for smooth movement
                steps = 20
                dx = (x - pos.x) / steps
                dy = (y - pos.y) / steps
                
                # Move in steps
                for i in range(steps):
                    new_x = pos.x + dx * (i + 1)
                    new_y = pos.y + dy * (i + 1)
                    Quartz.CGWarpMouseCursorPosition(
                        Quartz.CGPoint(new_x, new_y)
                    )
                    Quartz.CGDisplayMoveCursorToPoint(
                        0,
                        Quartz.CGPoint(new_x, new_y)
                    )
            else:
                # Move directly
                Quartz.CGWarpMouseCursorPosition(
                    Quartz.CGPoint(x, y)
                )
                Quartz.CGDisplayMoveCursorToPoint(
                    0,
                    Quartz.CGPoint(x, y)
                )
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to move mouse: {e}")
            return False
            
    def click(
        self,
        button: MouseButton = MouseButton.LEFT,
        double: bool = False
    ):
        """Simulate mouse click"""
        try:
            # Get current position
            pos = Quartz.CGEventGetLocation(
                Quartz.CGEventCreate(None)
            )
            
            # Create mouse events
            if button == MouseButton.LEFT:
                down = Quartz.CGEventCreateMouseEvent(
                    None,
                    Quartz.kCGEventLeftMouseDown,
                    pos,
                    Quartz.kCGMouseButtonLeft
                )
                up = Quartz.CGEventCreateMouseEvent(
                    None,
                    Quartz.kCGEventLeftMouseUp,
                    pos,
                    Quartz.kCGMouseButtonLeft
                )
            else:
                down = Quartz.CGEventCreateMouseEvent(
                    None,
                    Quartz.kCGEventRightMouseDown,
                    pos,
                    Quartz.kCGMouseButtonRight
                )
                up = Quartz.CGEventCreateMouseEvent(
                    None,
                    Quartz.kCGEventRightMouseUp,
                    pos,
                    Quartz.kCGMouseButtonRight
                )
                
            # Post events
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
            
            if double:
                # Post second click
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, down)
                Quartz.CGEventPost(Quartz.kCGHIDEventTap, up)
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to simulate click: {e}")
            return False
            
    def _handle_event(self, event: NSEvent):
        """Handle mouse event"""
        try:
            # Get position
            pos = event.locationInWindow()
            position = (int(pos.x), int(pos.y))
            
            # Determine button and state
            event_type = event.type()
            if event_type == NSEventMaskLeftMouseDown:
                button = MouseButton.LEFT
                is_pressed = True
            elif event_type == NSEventMaskLeftMouseUp:
                button = MouseButton.LEFT
                is_pressed = False
            elif event_type == NSEventMaskRightMouseDown:
                button = MouseButton.RIGHT
                is_pressed = True
            elif event_type == NSEventMaskRightMouseUp:
                button = MouseButton.RIGHT
                is_pressed = False
            else:
                button = None
                is_pressed = False
                
            # Create event info
            mouse_event = MouseEvent(
                position=position,
                button=button,
                is_pressed=is_pressed,
                timestamp=event.timestamp(),
                modifiers=self._get_modifiers(event)
            )
            
            # Call handlers
            for handler in self.handlers.values():
                handler(mouse_event)
                
        except Exception as e:
            logger.error(f"Failed to handle mouse event: {e}")
            
    def _get_modifiers(self, event: NSEvent) -> list[str]:
        """Get active modifier keys"""
        modifiers = []
        flags = event.modifierFlags()
        
        if flags & NSEvent.NSCommandKeyMask:
            modifiers.append('command')
        if flags & NSEvent.NSAlternateKeyMask:
            modifiers.append('option')
        if flags & NSEvent.NSControlKeyMask:
            modifiers.append('control')
        if flags & NSEvent.NSShiftKeyMask:
            modifiers.append('shift')
            
        return modifiers 