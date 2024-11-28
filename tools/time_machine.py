import subprocess
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class TimeMachineManager:
    """Manage Time Machine backups"""
    
    def get_backup_status(self) -> Dict:
        """Get current Time Machine status"""
        result = subprocess.run(['tmutil', 'status'], capture_output=True, text=True)
        status = {}
        
        for line in result.stdout.splitlines():
            if ':' in line:
                key, value = line.split(':', 1)
                status[key.strip()] = value.strip()
                
        return status
        
    def list_backups(self) -> List[Dict]:
        """List available Time Machine backups"""
        result = subprocess.run(['tmutil', 'listbackups'], capture_output=True, text=True)
        backups = []
        
        for line in result.stdout.splitlines():
            if line.strip():
                path = Path(line.strip())
                date = datetime.fromtimestamp(path.stat().st_mtime)
                backups.append({
                    'path': str(path),
                    'date': date,
                    'size': path.stat().st_size
                })
        return backups
        
    def start_backup(self) -> bool:
        """Start Time Machine backup"""
        result = subprocess.run(['tmutil', 'startbackup'])
        return result.returncode == 0
        
    def restore_file(self, file_path: str, backup_date: Optional[datetime] = None) -> bool:
        """Restore file from Time Machine backup"""
        cmd = ['tmutil', 'restore', file_path]
        
        if backup_date:
            # Find backup from date
            backups = self.list_backups()
            target_backup = None
            
            for backup in backups:
                if backup['date'].date() == backup_date.date():
                    target_backup = backup['path']
                    break
                    
            if target_backup:
                cmd.extend(['-backup', target_backup])
                
        result = subprocess.run(cmd)
        return result.returncode == 0 