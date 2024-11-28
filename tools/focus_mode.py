from Foundation import NSWorkspace, NSDate
import objc
from datetime import datetime, timedelta
from typing import List, Optional

class FocusModeManager:
    """Manage Focus modes and notifications"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        
    def get_focus_modes(self) -> List[dict]:
        """Get available Focus modes"""
        modes = []
        for mode in self.workspace.focusModes():
            modes.append({
                'id': mode.identifier(),
                'name': mode.name(),
                'is_active': mode.isActive(),
                'schedule': mode.schedule()
            })
        return modes
        
    def activate_focus(self, mode_id: str, 
                      duration: Optional[int] = None):
        """Activate specific Focus mode"""
        for mode in self.workspace.focusModes():
            if mode.identifier() == mode_id:
                if duration:
                    end_date = NSDate.dateWithTimeIntervalSinceNow_(
                        duration * 60
                    )
                    mode.activateUntilDate_(end_date)
                else:
                    mode.activate()
                break
                
    def set_focus_schedule(self, mode_id: str, 
                          start_time: datetime,
                          end_time: datetime,
                          days: List[str]):
        """Set Focus mode schedule"""
        schedule = {
            'startTime': start_time.strftime('%H:%M'),
            'endTime': end_time.strftime('%H:%M'),
            'days': days
        }
        
        for mode in self.workspace.focusModes():
            if mode.identifier() == mode_id:
                mode.setSchedule_(schedule)
                break 