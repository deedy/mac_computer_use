from AppKit import NSWorkspace, NSScreen
import Quartz

class AccessibilityManager:
    """Manage accessibility features"""
    
    def toggle_voiceover(self, enabled: bool):
        """Toggle VoiceOver screen reader"""
        script = f"""
        tell application "System Events"
            set voiceover to {str(enabled).lower()}
        end tell
        """
        self.run_applescript(script)
        
    def set_zoom_level(self, level: float):
        """Set screen zoom level"""
        Quartz.CGDisplaySetUserZoom(
            Quartz.CGMainDisplayID(),
            level
        )
        
    def increase_contrast(self, enabled: bool):
        """Toggle increased contrast"""
        script = f"""
        tell application "System Events"
            tell application "System Preferences"
                reveal anchor "Seeing" of pane "com.apple.preference.universalaccess"
            end tell
            tell process "System Preferences"
                set value of checkbox "Increase contrast" to {int(enabled)}
            end tell
        end tell
        """
        self.run_applescript(script) 