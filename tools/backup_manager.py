import tarfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

class BackupManager:
    """Manage backups of application data and configurations"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
    async def create_backup(self, name: str = None) -> Path:
        """Create a new backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = name or f"backup_{timestamp}"
        backup_path = self.backup_dir / f"{name}.tar.gz"
        
        # Backup important directories
        with tarfile.open(backup_path, "w:gz") as tar:
            tar.add("storage", arcname="storage")
            tar.add("logs", arcname="logs")
            tar.add(".env", arcname=".env")
            
        return backup_path
    
    async def restore_backup(self, backup_path: Path):
        """Restore from a backup"""
        # Create restore point before proceeding
        await self.create_backup("pre_restore")
        
        with tarfile.open(backup_path, "r:gz") as tar:
            tar.extractall(".")
            
    async def cleanup_old_backups(self, days: int = 30):
        """Remove backups older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        for backup in self.backup_dir.glob("*.tar.gz"):
            if backup.stat().st_mtime < cutoff.timestamp():
                backup.unlink() 