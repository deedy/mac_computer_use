from typing import Optional, Dict
from AppKit import (
    NSAlert,
    NSTextField,
    NSSecureTextField,
    NSApp,
    NSImage
)
import logging


logger = logging.getLogger(__name__)


class DialogManager:
    """Native macOS dialog management"""
    
    def show_alert(
        self,
        title: str,
        message: str,
        icon_path: Optional[str] = None,
        buttons: Optional[list[str]] = None
    ) -> Dict:
        """Show a native alert dialog"""
        try:
            alert = NSAlert.alloc().init()
            alert.setMessageText_(title)
            alert.setInformativeText_(message)
            
            # Add custom buttons if specified
            if buttons:
                for button in buttons:
                    alert.addButtonWithTitle_(button)
                    
            # Set custom icon if specified
            if icon_path:
                icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
                if icon:
                    alert.setIcon_(icon)
                    
            # Activate and show dialog
            NSApp.activateIgnoringOtherApps_(True)
            response = alert.runModal()
            
            return {
                'success': True,
                'button': response - 1000,  # Convert to 0-based index
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Failed to show alert: {e}")
            return {
                'success': False,
                'button': None,
                'error': str(e)
            }
            
    def show_input_dialog(
        self,
        title: str,
        message: str,
        secure: bool = False,
        default: str = "",
        icon_path: Optional[str] = None
    ) -> Dict:
        """Show a native input dialog"""
        try:
            alert = NSAlert.alloc().init()
            alert.setMessageText_(title)
            alert.setInformativeText_(message)
            
            # Create input field
            frame = ((0, 0), (300, 24))
            input_field = (
                NSSecureTextField if secure else NSTextField
            ).alloc().initWithFrame_(frame)
            input_field.setStringValue_(default)
            
            alert.setAccessoryView_(input_field)
            
            # Set custom icon if specified  
            if icon_path:
                icon = NSImage.alloc().initWithContentsOfFile_(icon_path)
                if icon:
                    alert.setIcon_(icon)
                    
            # Activate and show dialog
            NSApp.activateIgnoringOtherApps_(True)
            response = alert.runModal()
            
            if response == 1000:  # OK button
                return {
                    'success': True,
                    'value': input_field.stringValue(),
                    'error': None
                }
                
            return {
                'success': False,
                'value': None,
                'error': 'Cancelled'
            }
            
        except Exception as e:
            logger.error(f"Failed to show input dialog: {e}")
            return {
                'success': False,
                'value': None,
                'error': str(e)
            } 