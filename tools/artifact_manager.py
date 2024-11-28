import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import json
from dataclasses import dataclass, asdict
from .config import settings

@dataclass
class Artifact:
    """Represents a stored artifact"""
    filename: str
    original_path: str
    stored_path: str
    mime_type: str
    size_bytes: int
    created_at: str
    session_id: str
    description: Optional[str] = None

class ArtifactManager:
    """Manages storage and tracking of artifacts"""
    
    def __init__(self, base_dir: str = "storage/artifacts"):
        self.base_dir = Path(base_dir)
        self.index_file = self.base_dir / "artifact_index.json"
        self._ensure_storage()
        self.artifacts: Dict[str, List[Artifact]] = self._load_index()
    
    def _ensure_storage(self) -> None:
        """Ensure storage directory exists"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if not self.index_file.exists():
            self._save_index({})
    
    def _load_index(self) -> Dict[str, List[Artifact]]:
        """Load artifact index from disk"""
        if self.index_file.exists():
            with open(self.index_file) as f:
                data = json.load(f)
                return {
                    session_id: [Artifact(**a) for a in artifacts]
                    for session_id, artifacts in data.items()
                }
        return {}
    
    def _save_index(self, data: Dict[str, List[dict]]) -> None:
        """Save artifact index to disk"""
        with open(self.index_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def store_artifact(self, 
                      file_path: str | Path, 
                      session_id: str,
                      description: Optional[str] = None,
                      keep_original: bool = False) -> Artifact:
        """Store a new artifact"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Create session directory if needed
        session_dir = self.base_dir / session_id
        session_dir.mkdir(exist_ok=True)
        
        # Generate stored filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stored_filename = f"{timestamp}_{file_path.name}"
        stored_path = session_dir / stored_filename
        
        # Copy or move file
        if keep_original:
            shutil.copy2(file_path, stored_path)
        else:
            shutil.move(file_path, stored_path)
        
        # Create artifact record
        artifact = Artifact(
            filename=file_path.name,
            original_path=str(file_path),
            stored_path=str(stored_path),
            mime_type=self._get_mime_type(file_path),
            size_bytes=stored_path.stat().st_size,
            created_at=datetime.now().isoformat(),
            session_id=session_id,
            description=description
        )
        
        # Update index
        if session_id not in self.artifacts:
            self.artifacts[session_id] = []
        self.artifacts[session_id].append(artifact)
        self._save_index({
            sid: [asdict(a) for a in artifacts]
            for sid, artifacts in self.artifacts.items()
        })
        
        return artifact
    
    def get_session_artifacts(self, session_id: str) -> List[Artifact]:
        """Get all artifacts for a session"""
        return self.artifacts.get(session_id, [])
    
    def get_artifact(self, session_id: str, filename: str) -> Optional[Artifact]:
        """Get specific artifact by filename"""
        for artifact in self.artifacts.get(session_id, []):
            if artifact.filename == filename:
                return artifact
        return None
    
    def cleanup_old_artifacts(self, days: int = None) -> None:
        """Remove artifacts older than specified days"""
        if days is None:
            days = settings.ARTIFACT_RETENTION_DAYS
            
        cutoff = datetime.now() - timedelta(days=days)
        
        for session_id, artifacts in list(self.artifacts.items()):
            current_artifacts = []
            for artifact in artifacts:
                created_at = datetime.fromisoformat(artifact.created_at)
                if created_at > cutoff:
                    current_artifacts.append(artifact)
                else:
                    # Remove file
                    try:
                        os.remove(artifact.stored_path)
                    except FileNotFoundError:
                        pass
                        
            if current_artifacts:
                self.artifacts[session_id] = current_artifacts
            else:
                # Remove empty session
                del self.artifacts[session_id]
                try:
                    shutil.rmtree(self.base_dir / session_id)
                except FileNotFoundError:
                    pass
                    
        self._save_index({
            sid: [asdict(a) for a in artifacts]
            for sid, artifacts in self.artifacts.items()
        })
    
    @staticmethod
    def _get_mime_type(file_path: Path) -> str:
        """Get MIME type of file"""
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream' 