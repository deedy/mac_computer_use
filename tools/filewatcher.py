from typing import Optional, Callable
from AppKit import (
    NSWorkspace,
    NSMetadataQuery,
    NSNotificationCenter,
    NSMetadataQueryDidUpdateNotification
)
import logging


logger = logging.getLogger(__name__)


class FileWatcher:
    """Native macOS file system monitoring"""
    
    def __init__(self):
        self.workspace = NSWorkspace.sharedWorkspace()
        self.query = NSMetadataQuery.alloc().init()
        self.callbacks = {}
        
    def watch_path(
        self,
        path: str,
        callback: Callable,
        recursive: bool = True
    ) -> bool:
        """Watch a path for changes"""
        try:
            # Setup query
            self.query.setPredicate_(
                f"kMDItemPath == '{path}'"
            )
            self.query.setSearchScopes_([path])
            
            # Register callback
            self.callbacks[path] = callback
            
            # Start monitoring
            NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
                self,
                "handleQueryNotification:",
                NSMetadataQueryDidUpdateNotification,
                self.query
            )
            
            self.query.startQuery()
            return True
            
        except Exception as e:
            logger.error(f"Failed to watch path: {e}")
            return False
            
    def stop_watching(self, path: Optional[str] = None):
        """Stop watching path(s)"""
        try:
            if path:
                if path in self.callbacks:
                    del self.callbacks[path]
            else:
                self.callbacks.clear()
                
            if not self.callbacks:
                self.query.stopQuery()
                
        except Exception as e:
            logger.error(f"Failed to stop watching: {e}")
            
    def handleQueryNotification_(self, notification):
        """Handle file system change notification"""
        try:
            results = self.query.results()
            for result in results:
                path = result.valueForAttribute_("kMDItemPath")
                if path in self.callbacks:
                    self.callbacks[path](path)
        except Exception as e:
            logger.error(f"Failed to handle notification: {e}") 