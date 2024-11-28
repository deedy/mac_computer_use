from keyboard import add_hotkey, remove_hotkey
from typing import Callable

class HotkeyManager:
    """Global hotkey management"""
    
    def __init__(self):
        self.active_hotkeys = {}
        
    def register_hotkey(self, keys: str, callback: Callable):
        """Register a global hotkey"""
        add_hotkey(keys, callback)
        self.active_hotkeys[keys] = callback
        
    def unregister_hotkey(self, keys: str):
        """Remove a global hotkey"""
        if keys in self.active_hotkeys:
            remove_hotkey(keys)
            del self.active_hotkeys[keys] 