from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import json
from pathlib import Path
import logging
from datetime import datetime, time
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class CalibrationProfile:
    """Display calibration profile"""
    name: str
    settings: Dict[str, Any]
    created_at: datetime
    modified_at: datetime
    auto_switch: bool = False
    schedule: Optional[Dict[str, time]] = None
    metadata: Optional[Dict[str, Any]] = None

class CalibrationManager:
    """Manages display calibration profiles"""
    
    def __init__(self, storage_path: str = "storage/calibration"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.active_profiles: Dict[str, CalibrationProfile] = {}
        self._load_profiles()
        
    def _load_profiles(self):
        """Load saved calibration profiles"""
        try:
            for profile_file in self.storage_path.glob("*.json"):
                with open(profile_file, "r") as f:
                    data = json.load(f)
                    profile = CalibrationProfile(
                        name=data["name"],
                        settings=data["settings"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        modified_at=datetime.fromisoformat(data["modified_at"]),
                        auto_switch=data.get("auto_switch", False),
                        schedule=data.get("schedule"),
                        metadata=data.get("metadata")
                    )
                    self.active_profiles[profile.name] = profile
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")
            
    async def save_profile(self, profile: CalibrationProfile):
        """Save a calibration profile"""
        try:
            profile_path = self.storage_path / f"{profile.name}.json"
            profile_data = {
                "name": profile.name,
                "settings": profile.settings,
                "created_at": profile.created_at.isoformat(),
                "modified_at": profile.modified_at.isoformat(),
                "auto_switch": profile.auto_switch,
                "schedule": profile.schedule,
                "metadata": profile.metadata
            }
            
            with open(profile_path, "w") as f:
                json.dump(profile_data, f, indent=2)
                
            self.active_profiles[profile.name] = profile
            
        except Exception as e:
            logger.error(f"Failed to save profile {profile.name}: {e}")
            raise
            
    async def get_profile(self, name: str) -> Optional[CalibrationProfile]:
        """Get a calibration profile by name"""
        return self.active_profiles.get(name)
        
    async def delete_profile(self, name: str):
        """Delete a calibration profile"""
        try:
            profile_path = self.storage_path / f"{name}.json"
            if profile_path.exists():
                profile_path.unlink()
            self.active_profiles.pop(name, None)
        except Exception as e:
            logger.error(f"Failed to delete profile {name}: {e}")
            raise
            
    async def start_auto_switching(self):
        """Start monitoring for auto-switching profiles"""
        while True:
            try:
                current_time = datetime.now().time()
                
                for profile in self.active_profiles.values():
                    if profile.auto_switch and profile.schedule:
                        start_time = profile.schedule.get("start")
                        end_time = profile.schedule.get("end")
                        
                        if start_time <= current_time <= end_time:
                            # Apply profile
                            await self.apply_profile(profile.name)
                            
            except Exception as e:
                logger.error(f"Auto-switching error: {e}")
                
            await asyncio.sleep(60)  # Check every minute 