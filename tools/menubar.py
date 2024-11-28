from typing import Optional, Callable, Dict
from AppKit import (
    NSStatusBar,
    NSStatusItem,
    NSMenu,
    NSMenuItem,
    NSImage,
    NSVariableStatusItemLength
)
import logging


logger = logging.getLogger(__name__)


class MenuBarManager:
    """Native macOS menu bar management"""
    
    def __init__(self):
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        self.menu = NSMenu.alloc().init()
        self.status_item.setMenu_(self.menu)
        
    def set_title(self, title: str):
        """Set menu bar item title"""
        try:
            self.status_item.setTitle_(title)
        except Exception as e:
            logger.error(f"Failed to set title: {e}")
            
    def set_icon(self, icon_path: str):
        """Set menu bar item icon"""
        try:
            icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
            if icon:
                icon.setTemplate_(True)  # Support dark mode
                self.status_item.setImage_(icon)
        except Exception as e:
            logger.error(f"Failed to set icon: {e}")
            
    def add_menu_item(
        self,
        title: str,
        callback: Callable,
        key: Optional[str] = None
    ):
        """Add menu item with optional shortcut"""
        try:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                title, "menuItemClicked:", key or ""
            )
            item.setTarget_(self)
            item.setRepresentedObject_(callback)
            self.menu.addItem_(item)
        except Exception as e:
            logger.error(f"Failed to add menu item: {e}")
            
    def add_separator(self):
        """Add separator line to menu"""
        try:
            self.menu.addItem_(NSMenuItem.separatorItem())
        except Exception as e:
            logger.error(f"Failed to add separator: {e}")
            
    def clear_menu(self):
        """Remove all menu items"""
        try:
            while self.menu.numberOfItems() > 0:
                self.menu.removeItemAtIndex_(0)
        except Exception as e:
            logger.error(f"Failed to clear menu: {e}")
            
    def menuItemClicked_(self, sender):
        """Handle menu item click"""
        try:
            callback = sender.representedObject()
            if callback:
                callback()
        except Exception as e:
            logger.error(f"Failed to handle menu click: {e}") 