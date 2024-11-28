from Foundation import NSWorkspace
import GroupActivities
from typing import List, Optional, Callable

class SharePlayManager:
    """Manage SharePlay sessions"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        self.active_sessions = {}
        
    def start_session(self, activity_type: str, 
                     metadata: dict = None) -> str:
        """Start new SharePlay session"""
        session = GroupActivities.GRActivity.alloc().init()
        session.setType_(activity_type)
        
        if metadata:
            session.setMetadata_(metadata)
            
        session_id = session.identifier()
        self.active_sessions[session_id] = session
        session.activate()
        
        return session_id
        
    def join_session(self, session_id: str):
        """Join existing SharePlay session"""
        for session in GroupActivities.GRActivity.activeSessions():
            if session.identifier() == session_id:
                session.join()
                self.active_sessions[session_id] = session
                break
                
    def end_session(self, session_id: str):
        """End SharePlay session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].end()
            del self.active_sessions[session_id]
            
    def get_active_sessions(self) -> List[dict]:
        """Get active SharePlay sessions"""
        sessions = []
        for session in GroupActivities.GRActivity.activeSessions():
            sessions.append({
                'id': session.identifier(),
                'type': session.type(),
                'metadata': session.metadata(),
                'participants': len(session.participants())
            })
        return sessions 