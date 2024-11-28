from AppKit import NSPasteboard, NSStringPboardType
import logging


logger = logging.getLogger(__name__)


class ClipboardManager:
    """Native macOS clipboard management"""
    
    def __init__(self):
        self.pasteboard = NSPasteboard.generalPasteboard()
        
    def get_clipboard_text(self) -> str:
        """Get text content from clipboard"""
        try:
            return self.pasteboard.stringForType_(NSStringPboardType) or ""
        except Exception as e:
            logger.error(f"Failed to get clipboard text: {e}")
            return ""
            
    def set_clipboard_text(self, text: str) -> bool:
        """Set text content to clipboard"""
        try:
            self.pasteboard.clearContents()
            return self.pasteboard.setString_forType_(text, NSStringPboardType)
        except Exception as e:
            logger.error(f"Failed to set clipboard text: {e}")
            return False
            
    def clear_clipboard(self) -> bool:
        """Clear clipboard contents"""
        try:
            self.pasteboard.clearContents()
            return True
        except Exception as e:
            logger.error(f"Failed to clear clipboard: {e}")
            return False 