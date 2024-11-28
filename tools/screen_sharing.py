from typing import Dict, List, Optional
import subprocess
import logging
import json


logger = logging.getLogger(__name__)


class ScreenSharingManager:
    """Native macOS screen sharing management"""
    
    def get_shared_displays(self) -> List[Dict]:
        """Get list of displays being shared"""
        try:
            output = subprocess.check_output(
                ['system_profiler', 'SPDisplaysDataType', '-json']
            ).decode()
            data = json.loads(output)
            
            shared = []
            for display in data.get('SPDisplaysDataType', []):
                if display.get('sidecar_enabled') or display.get('airplay_enabled'):
                    shared.append({
                        'name': display['_name'],
                        'type': 'Sidecar' if display.get('sidecar_enabled')
                               else 'AirPlay',
                        'resolution': display.get('resolution'),
                        'refresh_rate': display.get('refresh_rate')
                    })
            return shared
            
        except Exception as e:
            logger.error(f"Failed to get shared displays: {e}")
            return []
            
    def start_sharing(self, display_id: int, mode: str = "airplay") -> bool:
        """Start screen sharing for display"""
        try:
            script = f'''
            tell application "System Events"
                tell process "ControlCenter"
                    click menu bar item "Screen Mirroring"
                    click menu item "{mode}" of menu 1
                end tell
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script], check=True)
            return True
            
        except Exception as e:
            logger.error(f"Failed to start sharing: {e}")
            return False
            
    def stop_sharing(self, display_id: int) -> bool:
        """Stop screen sharing for display"""
        try:
            script = '''
            tell application "System Events"
                tell process "ControlCenter"
                    click menu bar item "Screen Mirroring"
                    click menu item "Stop Mirroring" of menu 1
                end tell
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script], check=True)
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop sharing: {e}")
            return False 