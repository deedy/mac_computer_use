from typing import Optional, Dict, Any
from AppKit import (
    NSPasteboard,
    NSPasteboardTypeString,
    NSPasteboardTypePNG,
    NSPasteboardTypePDF,
    NSImage,
    NSData
)
import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class ClipboardManager:
    """Native macOS clipboard management"""
    
    def __init__(self):
        self.pasteboard = NSPasteboard.generalPasteboard()
        self.history: list[Dict[str, Any]] = []
        self.max_history = 100
        
    def get_text(self) -> Optional[str]:
        """Get text from clipboard"""
        try:
            return self.pasteboard.stringForType_(NSPasteboardTypeString)
        except Exception as e:
            logger.error(f"Failed to get clipboard text: {e}")
            return None
            
    def set_text(self, text: str) -> bool:
        """Set text to clipboard"""
        try:
            self.pasteboard.clearContents()
            success = self.pasteboard.setString_forType_(
                text,
                NSPasteboardTypeString
            )
            if success:
                self._add_to_history('text', text)
            return success
        except Exception as e:
            logger.error(f"Failed to set clipboard text: {e}")
            return False
            
    def get_image(self) -> Optional[NSImage]:
        """Get image from clipboard"""
        try:
            data = self.pasteboard.dataForType_(NSPasteboardTypePNG)
            if data:
                return NSImage.alloc().initWithData_(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get clipboard image: {e}")
            return None
            
    def set_image(self, image_path: Path) -> bool:
        """Set image to clipboard"""
        try:
            image = NSImage.alloc().initWithContentsOfFile_(str(image_path))
            if not image:
                return False
                
            self.pasteboard.clearContents()
            success = self.pasteboard.setData_forType_(
                image.TIFFRepresentation(),
                NSPasteboardTypePNG
            )
            if success:
                self._add_to_history('image', str(image_path))
            return success
        except Exception as e:
            logger.error(f"Failed to set clipboard image: {e}")
            return False
            
    def get_pdf(self) -> Optional[NSData]:
        """Get PDF data from clipboard"""
        try:
            return self.pasteboard.dataForType_(NSPasteboardTypePDF)
        except Exception as e:
            logger.error(f"Failed to get clipboard PDF: {e}")
            return None
            
    def set_pdf(self, pdf_path: Path) -> bool:
        """Set PDF to clipboard"""
        try:
            data = NSData.dataWithContentsOfFile_(str(pdf_path))
            if not data:
                return False
                
            self.pasteboard.clearContents()
            success = self.pasteboard.setData_forType_(
                data,
                NSPasteboardTypePDF
            )
            if success:
                self._add_to_history('pdf', str(pdf_path))
            return success
        except Exception as e:
            logger.error(f"Failed to set clipboard PDF: {e}")
            return False
            
    def clear(self) -> bool:
        """Clear clipboard contents"""
        try:
            self.pasteboard.clearContents()
            return True
        except Exception as e:
            logger.error(f"Failed to clear clipboard: {e}")
            return False
            
    def get_history(self) -> list[Dict[str, Any]]:
        """Get clipboard history"""
        return self.history
        
    def clear_history(self):
        """Clear clipboard history"""
        self.history = []
        
    def _add_to_history(self, type_: str, content: Any):
        """Add item to clipboard history"""
        self.history.append({
            'type': type_,
            'content': content
        })
        if len(self.history) > self.max_history:
            self.history.pop(0) 