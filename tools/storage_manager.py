from typing import Optional, Dict, List
from pathlib import Path
import shutil
import logging
from dataclasses import dataclass
from datetime import datetime
import json
import hashlib


logger = logging.getLogger(__name__)


@dataclass
class StorageMetrics:
    """Storage usage metrics"""
    total_bytes: int
    used_bytes: int
    free_bytes: int
    artifacts_count: int
    total_artifacts_size: int


@dataclass
class ArtifactInfo:
    """Information about a stored artifact"""
    id: str
    name: str
    path: Path
    size: int
    hash: str
    created: datetime
    metadata: Dict
    tags: List[str]


class StorageManager:
    """Native macOS file storage management"""
    
    def __init__(self, root_dir: Optional[Path] = None):
        self.root = root_dir or Path.home() / ".computer_use/storage"
        self.artifacts_dir = self.root / "artifacts"
        self.metadata_dir = self.root / "metadata"
        self._setup_storage()
        
    def _setup_storage(self):
        """Initialize storage directories"""
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
    def store_artifact(
        self,
        source_path: Path,
        name: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[ArtifactInfo]:
        """Store a file as an artifact"""
        try:
            # Generate artifact ID and paths
            artifact_id = self._generate_id(source_path)
            artifact_path = self.artifacts_dir / artifact_id
            meta_path = self.metadata_dir / f"{artifact_id}.json"
            
            # Copy file to artifacts directory
            shutil.copy2(source_path, artifact_path)
            
            # Calculate hash and size
            file_hash = self._calculate_hash(artifact_path)
            file_size = artifact_path.stat().st_size
            
            # Create artifact info
            info = ArtifactInfo(
                id=artifact_id,
                name=name or source_path.name,
                path=artifact_path,
                size=file_size,
                hash=file_hash,
                created=datetime.now(),
                metadata=metadata or {},
                tags=tags or []
            )
            
            # Save metadata
            self._save_metadata(info, meta_path)
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to store artifact: {e}")
            return None
            
    def get_artifact(self, artifact_id: str) -> Optional[ArtifactInfo]:
        """Get artifact information"""
        try:
            meta_path = self.metadata_dir / f"{artifact_id}.json"
            if not meta_path.exists():
                return None
                
            return self._load_metadata(meta_path)
            
        except Exception as e:
            logger.error(f"Failed to get artifact: {e}")
            return None
            
    def list_artifacts(
        self,
        tag: Optional[str] = None,
        name_pattern: Optional[str] = None
    ) -> List[ArtifactInfo]:
        """List stored artifacts with optional filtering"""
        try:
            artifacts = []
            for meta_file in self.metadata_dir.glob("*.json"):
                try:
                    info = self._load_metadata(meta_file)
                    
                    # Apply filters
                    if tag and tag not in info.tags:
                        continue
                    if name_pattern and name_pattern not in info.name:
                        continue
                        
                    artifacts.append(info)
                except Exception as e:
                    logger.error(f"Failed to load artifact {meta_file}: {e}")
                    continue
                    
            return artifacts
            
        except Exception as e:
            logger.error(f"Failed to list artifacts: {e}")
            return []
            
    def delete_artifact(self, artifact_id: str) -> bool:
        """Delete an artifact"""
        try:
            artifact_path = self.artifacts_dir / artifact_id
            meta_path = self.metadata_dir / f"{artifact_id}.json"
            
            # Remove files
            if artifact_path.exists():
                artifact_path.unlink()
            if meta_path.exists():
                meta_path.unlink()
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete artifact: {e}")
            return False
            
    def get_storage_metrics(self) -> StorageMetrics:
        """Get storage usage metrics"""
        try:
            # Get disk usage
            total, used, free = shutil.disk_usage(self.root)
            
            # Count artifacts
            artifacts = list(self.artifacts_dir.glob("*"))
            artifacts_size = sum(f.stat().st_size for f in artifacts)
            
            return StorageMetrics(
                total_bytes=total,
                used_bytes=used,
                free_bytes=free,
                artifacts_count=len(artifacts),
                total_artifacts_size=artifacts_size
            )
            
        except Exception as e:
            logger.error(f"Failed to get storage metrics: {e}")
            return StorageMetrics(0, 0, 0, 0, 0)
            
    def _generate_id(self, path: Path) -> str:
        """Generate unique artifact ID"""
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
        
    def _save_metadata(self, info: ArtifactInfo, path: Path):
        """Save artifact metadata to file"""
        data = {
            "id": info.id,
            "name": info.name,
            "path": str(info.path),
            "size": info.size,
            "hash": info.hash,
            "created": info.created.isoformat(),
            "metadata": info.metadata,
            "tags": info.tags
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
            
    def _load_metadata(self, path: Path) -> ArtifactInfo:
        """Load artifact metadata from file"""
        with open(path) as f:
            data = json.load(f)
            
        return ArtifactInfo(
            id=data["id"],
            name=data["name"],
            path=Path(data["path"]),
            size=data["size"],
            hash=data["hash"],
            created=datetime.fromisoformat(data["created"]),
            metadata=data["metadata"],
            tags=data["tags"]
        ) 