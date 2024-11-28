from Foundation import NSFileManager, NSURL
import os
from typing import List, Dict, Optional
from pathlib import Path

class iCloudManager:
    """Manage iCloud Drive integration"""
    
    def __init__(self):
        self.fm = NSFileManager.defaultManager()
        self.icloud_root = Path('~/Library/Mobile Documents/com~apple~CloudDocs').expanduser()
        
    def get_sync_status(self) -> Dict:
        """Get iCloud sync status"""
        status = {}
        
        # Check quota
        quota = self.fm.volumeAvailableCapacityForImportantUsageForURL_(
            NSURL.fileURLWithPath_(str(self.icloud_root))
        )
        status['available_space'] = quota
        
        # Check sync state
        status['syncing'] = self._is_syncing()
        status['pending_uploads'] = self._get_pending_uploads()
        
        return status
        
    def enable_sharing(self, file_path: str) -> Optional[str]:
        """Enable iCloud sharing for file"""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Move to iCloud if not already there
        if not str(path).startswith(str(self.icloud_root)):
            new_path = self.icloud_root / path.name
            os.rename(path, new_path)
            path = new_path
            
        # Generate sharing URL
        url = self.fm.URLForPublishingUbiquitousItemAtURL_expirationDate_error_(
            NSURL.fileURLWithPath_(str(path)),
            None,
            None
        )
        
        return str(url) if url else None
        
    def download_offline(self, file_path: str):
        """Download iCloud file for offline use"""
        path = Path(file_path)
        if not str(path).startswith(str(self.icloud_root)):
            raise ValueError("File is not in iCloud Drive")
            
        self.fm.startDownloadingUbiquitousItemAtURL_error_(
            NSURL.fileURLWithPath_(str(path)),
            None
        ) 