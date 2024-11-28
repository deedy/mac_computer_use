from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional
import sqlite3

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_REVIEW = "in_review"

@dataclass
class ApprovalRequest:
    """Represents a feature/change approval request"""
    id: str
    title: str
    description: str
    impact_areas: List[str]
    business_value: str
    technical_details: str
    rollback_plan: str
    pilot_results: Optional[str]
    created_at: datetime
    requested_by: str
    status: ApprovalStatus
    approvers: List[str]
    comments: List[dict]

class ApprovalManager:
    """Manages the approval workflow for new features and changes"""
    
    def __init__(self, db_path: str = "storage/approvals.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize approval tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    description TEXT,
                    impact_areas TEXT,
                    business_value TEXT,
                    technical_details TEXT,
                    rollback_plan TEXT,
                    pilot_results TEXT,
                    created_at TIMESTAMP,
                    requested_by TEXT,
                    status TEXT,
                    approvers TEXT,
                    comments TEXT
                )
            """)
            
    async def create_request(self, request: ApprovalRequest):
        """Create new approval request"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO approvals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    request.id,
                    request.title,
                    request.description,
                    ",".join(request.impact_areas),
                    request.business_value,
                    request.technical_details,
                    request.rollback_plan,
                    request.pilot_results,
                    request.created_at.isoformat(),
                    request.requested_by,
                    request.status.value,
                    ",".join(request.approvers),
                    str(request.comments)
                )
            )
            
    async def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get approval request details"""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT * FROM approvals WHERE id = ?", 
                (request_id,)
            ).fetchone()
            
        if result:
            return ApprovalRequest(
                id=result[0],
                title=result[1],
                description=result[2],
                impact_areas=result[3].split(","),
                business_value=result[4],
                technical_details=result[5],
                rollback_plan=result[6],
                pilot_results=result[7],
                created_at=datetime.fromisoformat(result[8]),
                requested_by=result[9],
                status=ApprovalStatus(result[10]),
                approvers=result[11].split(","),
                comments=eval(result[12])
            )
        return None
        
    async def update_status(self, request_id: str, status: ApprovalStatus, comment: str = None):
        """Update approval request status"""
        request = await self.get_request(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")
            
        if comment:
            request.comments.append({
                "timestamp": datetime.now().isoformat(),
                "comment": comment
            })
            
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """UPDATE approvals 
                   SET status = ?, comments = ?
                   WHERE id = ?""",
                (status.value, str(request.comments), request_id)
            ) 