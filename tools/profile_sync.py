from typing import Dict, List, Optional
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class ProfileSyncService:
    """Synchronize display profiles across devices"""
    
    def __init__(self, storage_dir: str = "storage/profiles"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.sync_interval = 300  # 5 minutes
        
    async def start_sync(self):
        """Start profile synchronization"""
        while True:
            try:
                await self._sync_profiles()
                await asyncio.sleep(self.sync_interval)
            except Exception as e:
                logger.error(f"Profile sync failed: {e}")
                
    async def _sync_profiles(self):
        """Synchronize profiles with remote storage"""
        try:
            # Get local profiles
            local_profiles = self._load_local_profiles()
            
            # Get remote profiles
            remote_profiles = await self._fetch_remote_profiles()
            
            # Compare and merge
            merged_profiles = self._merge_profiles(local_profiles, remote_profiles)
            
            # Save merged profiles
            await self._save_merged_profiles(merged_profiles)
            
            # Update remote storage
            await self._update_remote_storage(merged_profiles)
            
        except Exception as e:
            logger.error(f"Profile sync failed: {e}")
            raise
            
    def _merge_profiles(self, local: Dict, remote: Dict) -> Dict:
        """Merge local and remote profiles"""
        merged = {}
        
        # Compare timestamps and take newest version
        all_profile_ids = set(local.keys()) | set(remote.keys())
        
        for profile_id in all_profile_ids:
            local_profile = local.get(profile_id)
            remote_profile = remote.get(profile_id)
            
            if not local_profile:
                merged[profile_id] = remote_profile
            elif not remote_profile:
                merged[profile_id] = local_profile
            else:
                local_ts = datetime.fromisoformat(local_profile["modified_at"])
                remote_ts = datetime.fromisoformat(remote_profile["modified_at"])
                
                if local_ts >= remote_ts:
                    merged[profile_id] = local_profile
                else:
                    merged[profile_id] = remote_profile
                    
        return merged 