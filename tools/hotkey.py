from typing import Optional, Callable, Dict
from AppKit import (
    NSEvent,
    NSEventMaskKeyDown,
    NSApplication,
    NSKeyUp,
    NSFlagsChanged
)
import logging


logger = logging.getLogger(__name__)


class HotkeyManager:
    """Native macOS hotkey/keyboard shortcut management"""
    
    def __init__(self):
        self.hotkeys: Dict[str, Callable] = {}
        self.monitoring = False
        
    def register_hotkey(
        self,
        key: str,
        modifiers: list[str],
        callback: Callable
    ) -> bool:
        """Register a keyboard shortcut"""
        try:
            # Create hotkey identifier
            hotkey_id = self._make_hotkey_id(key, modifiers)
            self.hotkeys[hotkey_id] = callback
            
            # Start monitoring if not already
            if not self.monitoring:
                self._start_monitoring()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to register hotkey: {e}")
            return False
            
    def unregister_hotkey(self, key: str, modifiers: list[str]) -> bool:
        """Unregister a keyboard shortcut"""
        try:
            hotkey_id = self._make_hotkey_id(key, modifiers)
            if hotkey_id in self.hotkeys:
                del self.hotkeys[hotkey_id]
                
            # Stop monitoring if no hotkeys left
            if not self.hotkeys and self.monitoring:
                self._stop_monitoring()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister hotkey: {e}")
            return False
            
    def _make_hotkey_id(self, key: str, modifiers: list[str]) -> str:
        """Create unique identifier for hotkey"""
        return "+".join(sorted(modifiers) + [key])
        
    def _start_monitoring(self):
        """Start monitoring keyboard events"""
        try:
            NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                NSEventMaskKeyDown,
                self._handle_event
            )
            self.monitoring = True
        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            
    def _stop_monitoring(self):
        """Stop monitoring keyboard events"""
        try:
            NSEvent.removeMonitor_(self)
            self.monitoring = False
        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")
            
    def _handle_event(self, event: NSEvent):
        """Handle keyboard event"""
        try:
            # Get key and modifiers
            key = event.charactersIgnoringModifiers()
            modifiers = []
            
            flags = event.modifierFlags()
            if flags & NSEvent.NSCommandKeyMask:
                modifiers.append("command")
            if flags & NSEvent.NSAlternateKeyMask:
                modifiers.append("alt")
            if flags & NSEvent.NSControlKeyMask:
                modifiers.append("ctrl")
            if flags & NSEvent.NSShiftKeyMask:
                modifiers.append("shift")
                
            # Check if hotkey exists and call callback
            hotkey_id = self._make_hotkey_id(key, modifiers)
            if hotkey_id in self.hotkeys:
                self.hotkeys[hotkey_id]()
                
        except Exception as e:
            logger.error(f"Failed to handle event: {e}") 