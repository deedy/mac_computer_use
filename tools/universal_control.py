from Foundation import NSWorkspace
import Quartz
from typing import Tuple, List

class UniversalControlManager:
    """Manage Universal Control features for seamless device integration"""
    
    def get_connected_devices(self) -> List[dict]:
        """Get list of devices connected via Universal Control"""
        workspace = NSWorkspace.sharedWorkspace()
        devices = []
        
        # Query connected devices through private API
        for device in workspace.connectedDevices():
            devices.append({
                'name': device.name(),
                'type': device.deviceType(),
                'id': device.identifier(),
                'battery': device.batteryLevel(),
                'is_trusted': device.isTrusted()
            })
        return devices
        
    def get_cursor_position(self) -> Tuple[float, float]:
        """Get current cursor position across devices"""
        cursor = Quartz.CGEventGetLocation(
            Quartz.CGEventCreate(None)
        )
        return (cursor.x, cursor.y)
        
    def move_cursor_to_device(self, device_id: str, x: float, y: float):
        """Move cursor to specific position on target device"""
        workspace = NSWorkspace.sharedWorkspace()
        target_device = None
        
        # Find target device
        for device in workspace.connectedDevices():
            if device.identifier() == device_id:
                target_device = device
                break
                
        if target_device:
            # Move cursor using private API
            Quartz.CGWarpMouseCursorPosition(
                Quartz.CGPoint(x, y)
            ) 