from Foundation import NSWorkspace, NSURL
import objc
from pathlib import Path
from typing import List

class AirDropManager:
    """Manage AirDrop file sharing"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        
    def get_nearby_devices(self) -> List[dict]:
        """Get list of nearby AirDrop devices"""
        devices = []
        for device in self.workspace.nearbyDevices():
            devices.append({
                'name': device.name(),
                'type': device.deviceType(),
                'is_available': device.isAirDropAvailable()
            })
        return devices
        
    async def send_file(self, file_path: str, device_name: str):
        """Send file via AirDrop to specific device"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Find target device
        target = None
        for device in self.workspace.nearbyDevices():
            if device.name() == device_name:
                target = device
                break
                
        if not target:
            raise ValueError(f"Device not found: {device_name}")
            
        # Send file using private API
        url = NSURL.fileURLWithPath_(str(path))
        success = await self.workspace.sendFileViaAirDrop_toDevice_(
            url, target
        )
        
        if not success:
            raise RuntimeError(f"Failed to send file to {device_name}") 