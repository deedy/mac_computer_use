from Foundation import NSWorkspace, NSURL
import objc
from typing import List, Optional

class HandoffManager:
    """Manage Handoff/Continuity features"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        
    def get_available_activities(self) -> List[dict]:
        """Get list of available Handoff activities"""
        activities = []
        for activity in self.workspace.userActivities():
            activities.append({
                'type': activity.activityType(),
                'title': activity.title(),
                'webpage_url': activity.webpageURL(),
                'userInfo': activity.userInfo()
            })
        return activities
        
    def create_activity(self, activity_type: str, title: str, 
                       webpage_url: Optional[str] = None,
                       user_info: Optional[dict] = None):
        """Create new Handoff activity"""
        activity = NSUserActivity.alloc().initWithActivityType_(
            activity_type
        )
        activity.setTitle_(title)
        
        if webpage_url:
            activity.setWebpageURL_(NSURL.URLWithString_(webpage_url))
            
        if user_info:
            activity.addUserInfoEntriesFromDictionary_(user_info)
            
        activity.becomeCurrent()
        
    def resume_activity(self, activity_id: str):
        """Resume Handoff activity on this device"""
        for activity in self.workspace.userActivities():
            if activity.activityType() == activity_id:
                activity.becomeCurrent()
                break 