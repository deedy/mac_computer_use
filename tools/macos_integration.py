from Foundation import NSUserNotification, NSUserNotificationCenter
from AppKit import NSApplication, NSStatusBar, NSMenu, NSMenuItem
import objc

class MacOSIntegration:
    """Native macOS integration features"""
    
    def __init__(self):
        self.app = NSApplication.sharedApplication()
        self.setup_status_bar()
        
    def setup_status_bar(self):
        """Create status bar menu"""
        self.statusbar = NSStatusBar.systemStatusBar()
        self.statusitem = self.statusbar.statusItemWithLength_(30.0)
        
        # Create menu
        self.menu = NSMenu.alloc().init()
        self.menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            'Show', 'showWindow:', ''))
        self.menu.addItem_(NSMenuItem.separatorItem())
        self.menu.addItem_(NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            'Quit', 'terminate:', 'q'))
            
        self.statusitem.setMenu_(self.menu)
        
    def show_notification(self, title: str, message: str):
        """Show native macOS notification"""
        notification = NSUserNotification.alloc().init()
        notification.setTitle_(title)
        notification.setInformativeText_(message)
        
        center = NSUserNotificationCenter.defaultUserNotificationCenter()
        center.deliverNotification_(notification) 