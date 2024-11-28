from Foundation import NSWorkspace
import Quartz
from typing import List, Dict

class StageManagerControl:
    """Control Stage Manager window management"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        
    def get_stage_sets(self) -> List[Dict]:
        """Get current Stage Manager sets"""
        sets = []
        for stage in self.workspace.stageGroups():
            windows = []
            for window in stage.windows():
                windows.append({
                    'app': window.owningApplication().localizedName(),
                    'title': window.title(),
                    'id': window.windowID()
                })
            sets.append({
                'id': stage.identifier(),
                'name': stage.name(),
                'active': stage.isActive(),
                'windows': windows
            })
        return sets
        
    def create_stage(self, name: str, window_ids: List[int]) -> bool:
        """Create new Stage Manager set"""
        windows = []
        for window_id in window_ids:
            window = Quartz.CGWindowListCopyWindowInfo(
                Quartz.kCGWindowListOptionIncludingWindow,
                window_id
            )
            if window:
                windows.append(window)
                
        if windows:
            return self.workspace.createStageGroup_withWindows_(
                name, windows
            )
        return False
        
    def switch_stage(self, stage_id: str):
        """Switch to specific Stage Manager set"""
        for stage in self.workspace.stageGroups():
            if stage.identifier() == stage_id:
                stage.activate()
                break 