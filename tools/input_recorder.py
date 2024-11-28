from typing import List, Dict, Optional
import keyboard
import pyautogui
import logging
from dataclasses import dataclass
from datetime import datetime


logger = logging.getLogger(__name__)


@dataclass
class InputEvent:
    """Keyboard or mouse input event"""
    type: str  # 'key' or 'mouse'
    action: str  # 'press', 'release', 'click', 'move'
    time: datetime
    data: Dict  # Key name or mouse coordinates


class InputRecorder:
    """Record keyboard and mouse events"""
    
    def __init__(self):
        self.events: List[InputEvent] = []
        self.recording = False
        
    def start_recording(self):
        """Start recording input events"""
        try:
            self.events = []
            self.recording = True
            
            keyboard.hook(self._on_keyboard_event)
            pyautogui.FAILSAFE = False
            
            logger.info("Started input recording")
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.recording = False
            
    def stop_recording(self) -> List[InputEvent]:
        """Stop recording and return events"""
        try:
            self.recording = False
            keyboard.unhook_all()
            
            logger.info(f"Stopped recording with {len(self.events)} events")
            return self.events
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return []
            
    def _on_keyboard_event(self, event):
        """Handle keyboard events"""
        if self.recording:
            self.events.append(InputEvent(
                type='key',
                action=event.event_type,
                time=datetime.now(),
                data={'key': event.name}
            ))
            
    def _on_mouse_event(self, x: int, y: int, button: str, pressed: bool):
        """Handle mouse events"""
        if self.recording:
            self.events.append(InputEvent(
                type='mouse',
                action='press' if pressed else 'release',
                time=datetime.now(),
                data={
                    'x': x,
                    'y': y,
                    'button': button
                }
            )) 