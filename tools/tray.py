import rumps

class SystemTrayApp(rumps.App):
    """macOS system tray integration"""
    
    def __init__(self):
        super().__init__("Mac Computer Use")
        self.menu = [
            rumps.MenuItem("Start"),
            rumps.MenuItem("Stop"),
            rumps.MenuItem("Settings"),
            None,  # Separator
            rumps.MenuItem("Quit")
        ]
    
    @rumps.clicked("Start")
    def start(self, _):
        # Start the application
        pass
        
    @rumps.clicked("Settings")
    def settings(self, _):
        # Open settings window
        pass 