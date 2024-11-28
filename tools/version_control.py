from typing import Optional, Dict, List
from pathlib import Path
import shutil
import logging
from dataclasses import dataclass
from datetime import datetime
import json
import hashlib
import difflib
from enum import Enum


logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Types of file changes"""
    CREATED = 'created'
    MODIFIED = 'modified'
    DELETED = 'deleted'
    RENAMED = 'renamed'


@dataclass
class FileVersion:
    """Information about a file version"""
    version_id: str
    original_path: Path
    version_path: Path
    timestamp: datetime
    hash: str
    size: int
    change_type: ChangeType
    diff_from_previous: Optional[str] = None
    metadata: Dict = None


class VersionControl:
    """Native macOS version control system"""
    
    def __init__(self, root_dir: Optional[Path] = None):
        self.root = root_dir or Path.home() / ".computer_use/versions"
        self.versions_dir = self.root / "versions"
        self.metadata_dir = self.root / "metadata"
        self._setup_storage()
        
    def _setup_storage(self):
        """Initialize version control directories"""
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
    def create_version(
        self,
        file_path: Path,
        change_type: ChangeType = ChangeType.MODIFIED,
        metadata: Optional[Dict] = None
    ) -> Optional[FileVersion]:
        """Create a new version of a file"""
        try:
            # Generate version ID and paths
            version_id = self._generate_version_id(file_path)
            version_path = self.versions_dir / version_id
            meta_path = self.metadata_dir / f"{version_id}.json"
            
            # Copy file to versions directory
            shutil.copy2(file_path, version_path)
            
            # Calculate hash and size
            file_hash = self._calculate_hash(version_path)
            file_size = version_path.stat().st_size
            
            # Get diff from previous version if exists
            diff = None
            prev_version = self.get_latest_version(file_path)
            if prev_version and change_type == ChangeType.MODIFIED:
                diff = self._generate_diff(prev_version.version_path, version_path)
            
            # Create version info
            version = FileVersion(
                version_id=version_id,
                original_path=file_path,
                version_path=version_path,
                timestamp=datetime.now(),
                hash=file_hash,
                size=file_size,
                change_type=change_type,
                diff_from_previous=diff,
                metadata=metadata or {}
            )
            
            # Save metadata
            self._save_metadata(version, meta_path)
            
            return version
            
        except Exception as e:
            logger.error(f"Failed to create version: {e}")
            return None
            
    def get_version_history(
        self,
        file_path: Path,
        limit: Optional[int] = None
    ) -> List[FileVersion]:
        """Get version history for a file"""
        try:
            versions = []
            for meta_file in self.metadata_dir.glob("*.json"):
                try:
                    version = self._load_metadata(meta_file)
                    if version.original_path == file_path:
                        versions.append(version)
                except Exception as e:
                    logger.error(f"Failed to load version {meta_file}: {e}")
                    continue
                    
            # Sort by timestamp descending
            versions.sort(key=lambda v: v.timestamp, reverse=True)
            
            if limit:
                versions = versions[:limit]
                
            return versions
            
        except Exception as e:
            logger.error(f"Failed to get version history: {e}")
            return []
            
    def restore_version(
        self,
        version_id: str,
        restore_path: Optional[Path] = None
    ) -> bool:
        """Restore a specific version"""
        try:
            version = self.get_version(version_id)
            if not version:
                return False
                
            restore_to = restore_path or version.original_path
            shutil.copy2(version.version_path, restore_to)
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore version: {e}")
            return False
            
    def get_version(self, version_id: str) -> Optional[FileVersion]:
        """Get specific version information"""
        try:
            meta_path = self.metadata_dir / f"{version_id}.json"
            if not meta_path.exists():
                return None
                
            return self._load_metadata(meta_path)
            
        except Exception as e:
            logger.error(f"Failed to get version: {e}")
            return None
            
    def get_latest_version(self, file_path: Path) -> Optional[FileVersion]:
        """Get latest version of a file"""
        versions = self.get_version_history(file_path, limit=1)
        return versions[0] if versions else None
            
    def compare_versions(
        self,
        version_id1: str,
        version_id2: str
    ) -> Optional[str]:
        """Compare two versions"""
        try:
            v1 = self.get_version(version_id1)
            v2 = self.get_version(version_id2)
            
            if not v1 or not v2:
                return None
                
            return self._generate_diff(v1.version_path, v2.version_path)
            
        except Exception as e:
            logger.error(f"Failed to compare versions: {e}")
            return None
            
    def _generate_version_id(self, path: Path) -> str:
        """Generate unique version ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_hash = hashlib.sha256(str(path).encode()).hexdigest()[:8]
        return f"{timestamp}_{name_hash}"
        
    def _calculate_hash(self, path: Path) -> str:
        """Calculate file hash"""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
        
    def _generate_diff(self, path1: Path, path2: Path) -> str:
        """Generate diff between two files"""
        with open(path1) as f1, open(path2) as f2:
            diff = difflib.unified_diff(
                f1.readlines(),
                f2.readlines(),
                fromfile=str(path1),
                tofile=str(path2)
            )
            return ''.join(diff)
            
    def _save_metadata(self, version: FileVersion, path: Path):
        """Save version metadata to file"""
        data = {
            "version_id": version.version_id,
            "original_path": str(version.original_path),
            "version_path": str(version.version_path),
            "timestamp": version.timestamp.isoformat(),
            "hash": version.hash,
            "size": version.size,
            "change_type": version.change_type,
            "diff_from_previous": version.diff_from_previous,
            "metadata": version.metadata
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            
    def _load_metadata(self, path: Path) -> FileVersion:
        """Load version metadata from file"""
        with open(path) as f:
            data = json.load(f)
            
        return FileVersion(
            version_id=data["version_id"],
            original_path=Path(data["original_path"]),
            version_path=Path(data["version_path"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            hash=data["hash"],
            size=data["size"],
            change_type=ChangeType(data["change_type"]),
            diff_from_previous=data["diff_from_previous"],
            metadata=data["metadata"]
        ) 