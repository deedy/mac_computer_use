from typing import Dict, Optional, List
import subprocess
import logging
import json


logger = logging.getLogger(__name__)


class VolumeManager:
    """Native macOS volume/audio management"""
    
    def get_volume(self) -> Optional[int]:
        """Get system volume (0-100)"""
        try:
            output = subprocess.check_output(
                ['osascript', '-e', 'output volume of (get volume settings)']
            ).decode()
            return int(output)
        except Exception as e:
            logger.error(f"Failed to get volume: {e}")
            return None
            
    def set_volume(self, level: int) -> bool:
        """Set system volume (0-100)"""
        try:
            subprocess.run(
                ['osascript', '-e', f'set volume output volume {level}'],
                check=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
            return False
            
    def mute(self) -> bool:
        """Mute audio"""
        try:
            subprocess.run(
                ['osascript', '-e', 'set volume output muted true'],
                check=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to mute: {e}")
            return False
            
    def unmute(self) -> bool:
        """Unmute audio"""
        try:
            subprocess.run(
                ['osascript', '-e', 'set volume output muted false'],
                check=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to unmute: {e}")
            return False
            
    def get_input_devices(self) -> List[Dict]:
        """Get available audio input devices"""
        try:
            devices = []
            output = subprocess.check_output(
                ['system_profiler', 'SPAudioDataType', '-json']
            ).decode()
            data = json.loads(output)
            
            for device in data['SPAudioDataType']:
                if device.get('coreaudio_input', False):
                    devices.append({
                        'name': device['_name'],
                        'id': device.get('coreaudio_device_id'),
                        'built_in': device.get('coreaudio_device_transport') == 'built-in'
                    })
                    
            return devices
            
        except Exception as e:
            logger.error(f"Failed to get input devices: {e}")
            return [] 