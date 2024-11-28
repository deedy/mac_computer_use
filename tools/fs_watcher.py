from typing import Optional, Dict, Callable
from AppKit import (
    NSWorkspace,
    NSMetadataQuery,
    NSNotificationCenter,
    NSMetadataQueryDidUpdateNotification
)
import logging
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


logger = logging.getLogger(__name__)


class FileEvent(str, Enum):
    """File system event types"""
    CREATED = 'created'
    MODIFIED = 'modified'
    DELETED = 'deleted'
    RENAMED = 'renamed'
    MOVED = 'moved'


@dataclass
class FileChange:
    """File system change information"""
    event: FileEvent
    path: Path
    timestamp: datetime
    is_directory: bool
    old_path: Optional[Path] = None


class FileSystemWatcher:
    """Native macOS file system monitoring"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        self.query = NSMetadataQuery.alloc().init()
        self.handlers: Dict[str, Callable] = {}
        self._setup_monitoring()
        
    def _setup_monitoring(self):
        """Setup file system monitoring"""
        center = NSNotificationCenter.defaultCenter()
        center.addObserver_selector_name_object_(
            self,
            'handleQueryNotification:',
            NSMetadataQueryDidUpdateNotification,
            self.query
        )
        
    def watch_path(
        self,
        path: Path,
        callback: Callable[[FileChange], None],
        recursive: bool = True
    ) -> bool:
        """Watch path for changes"""
        try:
            # Setup query predicate
            predicate = f"kMDItemPath BEGINSWITH '{path}'"
            if not recursive:
                predicate += f" && kMDItemPath ENDSWITH '{path}'"
                
            self.query.setPredicate_(predicate)
            self.query.setSearchScopes_([str(path)])
            
            # Register callback
            self.handlers[str(path)] = callback
            
            # Start monitoring
            self.query.startQuery()
            logger.info(f"Started watching {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to watch path: {e}")
            return False
            
    def stop_watching(self, path: Optional[Path] = None):
        """Stop watching path(s)"""
        try:
            if path:
                path_str = str(path)
                if path_str in self.handlers:
                    del self.handlers[path_str]
                    logger.info(f"Stopped watching {path}")
            else:
                self.handlers.clear()
                logger.info("Stopped watching all paths")
                
            if not self.handlers:
                self.query.stopQuery()
                
        except Exception as e:
            logger.error(f"Failed to stop watching: {e}")
            
    def handleQueryNotification_(self, notification):
        """Handle file system change notification"""
        try:
            results = self.query.results()
            for result in results:
                path = Path(result.valueForAttribute_("kMDItemPath"))
                
                # Determine event type
                event = FileEvent.MODIFIED
                if not path.exists():
                    event = FileEvent.DELETED
                elif result.valueForAttribute_("kMDItemIsNew"):
                    event = FileEvent.CREATED
                    
                # Create change info
                change = FileChange(
                    event=event,
                    path=path,
                    timestamp=datetime.now(),
                    is_directory=path.is_dir()
                )
                
                # Call handlers
                for watched_path, handler in self.handlers.items():
                    if str(path).startswith(watched_path):
                        handler(change)
                        
        except Exception as e:
            logger.error(f"Failed to handle file change: {e}") 