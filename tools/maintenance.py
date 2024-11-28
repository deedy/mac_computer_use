import sqlite3
from datetime import datetime, timedelta
from .config import settings
from .artifact_manager import ArtifactManager

class MaintenanceTask:
    """Maintenance tasks for the application"""
    
    @staticmethod
    async def cleanup_old_chat_history():
        """Remove chat history older than retention period"""
        retention_date = datetime.now() - timedelta(days=settings.HISTORY_RETENTION_DAYS)
        
        with sqlite3.connect(settings.CHAT_HISTORY_DB_PATH) as conn:
            conn.execute(
                "DELETE FROM chat_history WHERE created_at < ?",
                (retention_date.isoformat(),)
            )
            conn.commit() 
    
    @staticmethod
    async def cleanup_old_data():
        """Remove old chat history and artifacts"""
        # Existing chat history cleanup
        await MaintenanceTask.cleanup_old_chat_history()
        
        # Cleanup artifacts
        artifact_manager = ArtifactManager()
        artifact_manager.cleanup_old_artifacts() 