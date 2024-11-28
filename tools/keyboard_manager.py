from typing import Optional, Dict, Callable
from AppKit import (
    NSEvent,
    NSEventMaskKeyDown,
    NSEventMaskKeyUp,
    NSEventMaskFlagsChanged
)
import logging
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class KeyModifier(str, Enum):
    """Keyboard modifiers"""
    COMMAND = 'command'
    OPTION = 'option'
    CONTROL = 'control'
    SHIFT = 'shift'
    FUNCTION = 'function'
    CAPSLOCK = 'capslock'


@dataclass
class KeyEvent:
    """Keyboard event information"""
    key: str
    modifiers: list[KeyModifier]
    is_pressed: bool
    timestamp: float
    repeat: bool = False


class KeyboardManager:
    """Native macOS keyboard management"""
    
    def __init__(self):
        self.handlers: Dict[str, Callable] = {}
        self.monitoring = False
        self._setup_monitoring()
        
    def _setup_monitoring(self):
        """Setup keyboard event monitoring"""
        mask = (
            NSEventMaskKeyDown |
            NSEventMaskKeyUp |
            NSEventMaskFlagsChanged
        )
        NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            mask,
            self._handle_event
        )
        self.monitoring = True
        
    def register_handler(
        self,
        key: str,
        modifiers: list[KeyModifier],
        callback: Callable[[KeyEvent], None]
    ):
        """Register keyboard event handler"""
        try:
            handler_id = self._make_handler_id(key, modifiers)
            self.handlers[handler_id] = callback
            logger.info(f"Registered handler for {handler_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register handler: {e}")
            return False
            
    def unregister_handler(self, key: str, modifiers: list[KeyModifier]):
        """Unregister keyboard event handler"""
        try:
            handler_id = self._make_handler_id(key, modifiers)
            if handler_id in self.handlers:
                del self.handlers[handler_id]
                logger.info(f"Unregistered handler for {handler_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to unregister handler: {e}")
            return False
            
    def _make_handler_id(self, key: str, modifiers: list[KeyModifier]) -> str:
        """Create unique handler identifier"""
        mod_str = "+".join(sorted(m.value for m in modifiers))
        return f"{mod_str}+{key}" if mod_str else key
        
    def _handle_event(self, event: NSEvent):
        """Handle keyboard event"""
        try:
            # Get key and modifiers
            key = event.charactersIgnoringModifiers()
            modifiers = self._get_active_modifiers(event)
            
            # Create event info
            key_event = KeyEvent(
                key=key,
                modifiers=modifiers,
                is_pressed=event.type() == NSEventMaskKeyDown,
                timestamp=event.timestamp(),
                repeat=event.isARepeat()
            )
            
            # Find and call handler
            handler_id = self._make_handler_id(key, modifiers)
            if handler_id in self.handlers:
                self.handlers[handler_id](key_event)
                
        except Exception as e:
            logger.error(f"Failed to handle keyboard event: {e}")
            
    def _get_active_modifiers(self, event: NSEvent) -> list[KeyModifier]:
        """Get list of active modifiers"""
        modifiers = []
        flags = event.modifierFlags()
        
        if flags & NSEvent.NSCommandKeyMask:
            modifiers.append(KeyModifier.COMMAND)
        if flags & NSEvent.NSAlternateKeyMask:
            modifiers.append(KeyModifier.OPTION)
        if flags & NSEvent.NSControlKeyMask:
            modifiers.append(KeyModifier.CONTROL)
        if flags & NSEvent.NSShiftKeyMask:
            modifiers.append(KeyModifier.SHIFT)
        if flags & NSEvent.NSFunctionKeyMask:
            modifiers.append(KeyModifier.FUNCTION)
        if flags & NSEvent.NSAlphaShiftKeyMask:
            modifiers.append(KeyModifier.CAPSLOCK)
            
        return modifiers 