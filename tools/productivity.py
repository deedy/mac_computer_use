import pyperclip
import schedule
import time
from pynput import keyboard, mouse
from typing import Optional, Dict, List
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class ProductivityManager:
    """Manage productivity features and tracking"""
    
    def __init__(self):
        self.clipboard_history: List[str] = []
        self.active_window_time: Dict[str, float] = {}
        self.current_window: Optional[str] = None
        self.start_time: float = time.time()
        
        try:
            # Initialize keyboard and mouse listeners
            self.keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                suppress=False  # Don't suppress events
            )
            self.mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                suppress=False  # Don't suppress events
            )
            
            # Start monitoring
            self.keyboard_listener.start()
            self.mouse_listener.start()
        except Exception as e:
            logger.error(f"Error initializing listeners: {e}")
            # Continue without listeners if they fail
            self.keyboard_listener = None
            self.mouse_listener = None
        
    def _on_key_press(self, key):
        """Track keyboard activity"""
        try:
            # Update active window time
            if self.current_window:
                elapsed = time.time() - self.start_time
                self.active_window_time[self.current_window] = \
                    self.active_window_time.get(self.current_window, 0) + elapsed
                
            # Track clipboard changes - do this less frequently
            if hasattr(key, 'char') and key.char in ['c', 'v'] and \
               any(mod for mod in keyboard.Controller().alt_pressed):
                clipboard_content = pyperclip.paste()
                if clipboard_content and clipboard_content not in self.clipboard_history:
                    self.clipboard_history.append(clipboard_content)
                    if len(self.clipboard_history) > 100:  # Keep last 100 items
                        self.clipboard_history.pop(0)
                    
        except Exception as e:
            logger.error(f"Error tracking keyboard: {e}")
            
    def _on_mouse_move(self, x, y):
        """Track mouse activity"""
        try:
            # Update current window based on mouse position
            window = self._get_window_at_position(x, y)
            if window != self.current_window:
                if self.current_window:
                    elapsed = time.time() - self.start_time
                    self.active_window_time[self.current_window] = \
                        self.active_window_time.get(self.current_window, 0) + elapsed
                self.current_window = window
                self.start_time = time.time()
                
        except Exception as e:
            logger.error(f"Error tracking mouse: {e}")
            
    def _get_window_at_position(self, x: int, y: int) -> Optional[str]:
        """Get window title at mouse position"""
        try:
            # Use Quartz/ApplicationServices to get window info
            from Quartz import (
                CGWindowListCopyWindowInfo,
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID
            )
            
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID
            )
            
            for window in window_list:
                bounds = window.get('kCGWindowBounds')
                if bounds:
                    if bounds.get('X', 0) <= x <= bounds.get('X', 0) + bounds.get('Width', 0) and \
                       bounds.get('Y', 0) <= y <= bounds.get('Y', 0) + bounds.get('Height', 0):
                        return window.get('kCGWindowOwnerName', 'Unknown')
            return None
            
        except Exception as e:
            logger.error(f"Error getting window info: {e}")
            return None
        
    def get_productivity_stats(self) -> Dict:
        """Get productivity statistics"""
        try:
            total_time = sum(self.active_window_time.values())
            
            return {
                'active_windows': {
                    window: round(time / total_time * 100, 2)
                    for window, time in self.active_window_time.items()
                },
                'clipboard_items': len(self.clipboard_history),
                'total_active_time': round(total_time / 60, 2),  # Minutes
                'current_window': self.current_window
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
            
    def save_stats(self, filepath: Optional[str] = None):
        """Save productivity stats to file"""
        try:
            stats = self.get_productivity_stats()
            
            if not filepath:
                filepath = Path.home() / '.productivity_stats.json'
                
            with open(filepath, 'w') as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
            
    def schedule_breaks(self, interval_mins: int = 45):
        """Schedule productivity breaks"""
        def notify_break():
            # Implementation depends on OS notifications
            pass
            
        schedule.every(interval_mins).minutes.do(notify_break)
        
    def clear_history(self):
        """Clear tracking history"""
        self.clipboard_history.clear()
        self.active_window_time.clear()
        self.current_window = None
        self.start_time = time.time() 