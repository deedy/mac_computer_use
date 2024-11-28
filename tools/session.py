import time
import uuid
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import jwt
from .config import settings
from .logging_config import logger
from .approval_manager import ApprovalStatus, ApprovalRequest

class SessionManager:
    """Manages user sessions and authentication"""
    
    # Store active sessions
    _sessions: Dict[str, Dict] = {}
    
    # Store pending approvals
    _pending_approvals: Dict[str, ApprovalRequest] = {}
    
    # JWT settings
    JWT_SECRET = str(uuid.uuid4())  # Generate random secret on startup
    JWT_ALGORITHM = "HS256"
    
    @classmethod
    def create_session(cls, user_id: str) -> str:
        """Create a new session for a user"""
        session_id = str(uuid.uuid4())
        expiry = datetime.utcnow() + timedelta(seconds=settings.SESSION_TIMEOUT)
        
        session_data = {
            "user_id": user_id,
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expiry.isoformat(),
            "last_activity": time.time()
        }
        
        # Store session
        cls._sessions[session_id] = session_data
        
        # Create JWT token
        token = jwt.encode(
            {
                "sub": user_id,
                "session_id": session_id,
                "exp": expiry
            },
            cls.JWT_SECRET,
            algorithm=cls.JWT_ALGORITHM
        )
        
        logger.info(f"Created session for user {user_id}")
        return token
    
    @classmethod
    def validate_session(cls, token: str) -> Optional[Dict]:
        """Validate a session token"""
        try:
            # Decode and validate JWT
            payload = jwt.decode(
                token,
                cls.JWT_SECRET,
                algorithms=[cls.JWT_ALGORITHM]
            )
            
            session_id = payload.get("session_id")
            session = cls._sessions.get(session_id)
            
            if not session:
                logger.warning(f"Session not found: {session_id}")
                return None
                
            # Check if session has expired
            expiry = datetime.fromisoformat(session["expires_at"])
            if datetime.utcnow() > expiry:
                logger.warning(f"Session expired: {session_id}")
                cls.end_session(session_id)
                return None
                
            # Update last activity
            session["last_activity"] = time.time()
            return session
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return None
    
    @classmethod
    def end_session(cls, session_id: str) -> None:
        """End a session"""
        if session_id in cls._sessions:
            session = cls._sessions.pop(session_id)
            logger.info(f"Ended session for user {session['user_id']}")
    
    @classmethod
    def cleanup_expired_sessions(cls) -> None:
        """Clean up expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = [
            session_id
            for session_id, session in cls._sessions.items()
            if current_time > datetime.fromisoformat(session["expires_at"])
        ]
        
        for session_id in expired_sessions:
            cls.end_session(session_id)
            
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    @classmethod
    def refresh_session(cls, token: str) -> Optional[str]:
        """Refresh a session token"""
        session = cls.validate_session(token)
        if not session:
            return None
            
        # Create new token with extended expiry
        new_expiry = datetime.utcnow() + timedelta(seconds=settings.SESSION_TIMEOUT)
        session["expires_at"] = new_expiry.isoformat()
        
        new_token = jwt.encode(
            {
                "sub": session["user_id"],
                "session_id": session["session_id"],
                "exp": new_expiry
            },
            cls.JWT_SECRET,
            algorithm=cls.JWT_ALGORITHM
        )
        
        logger.info(f"Refreshed session for user {session['user_id']}")
        return new_token

    @classmethod
    async def get_pending_approvals(cls) -> List[ApprovalRequest]:
        """Get list of pending approval requests."""
        return list(cls._pending_approvals.values())

    @classmethod
    async def create_approval_request(cls, request: ApprovalRequest) -> str:
        """Create a new approval request."""
        request_id = str(uuid.uuid4())
        request.id = request_id
        cls._pending_approvals[request_id] = request
        logger.info(f"Created approval request: {request_id}")
        return request_id

    @classmethod
    async def approve_request(cls, request_id: str) -> bool:
        """Approve a pending request."""
        if request_id not in cls._pending_approvals:
            logger.warning(f"Approval request not found: {request_id}")
            return False
        
        request = cls._pending_approvals[request_id]
        request.status = ApprovalStatus.APPROVED
        request.approved_at = datetime.utcnow().isoformat()
        logger.info(f"Approved request: {request_id}")
        return True

    @classmethod
    async def reject_request(cls, request_id: str) -> bool:
        """Reject a pending request."""
        if request_id not in cls._pending_approvals:
            logger.warning(f"Approval request not found: {request_id}")
            return False
        
        request = cls._pending_approvals[request_id]
        request.status = ApprovalStatus.REJECTED
        request.rejected_at = datetime.utcnow().isoformat()
        logger.info(f"Rejected request: {request_id}")
        return True

    @classmethod
    async def cleanup_old_approvals(cls) -> None:
        """Clean up old approval requests."""
        current_time = datetime.utcnow()
        cutoff = current_time - timedelta(days=settings.APPROVAL_RETENTION_DAYS)
        
        old_requests = [
            request_id
            for request_id, request in cls._pending_approvals.items()
            if datetime.fromisoformat(request.created_at) < cutoff
        ]
        
        for request_id in old_requests:
            del cls._pending_approvals[request_id]
            
        if old_requests:
            logger.info(f"Cleaned up {len(old_requests)} old approval requests")