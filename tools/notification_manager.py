from typing import Optional
from AppKit import (
    NSUserNotification,
    NSUserNotificationCenter,
    NSImage
)
import logging


logger = logging.getLogger(__name__)


class NotificationManager:
    """Native macOS notification management"""
    
    def __init__(self):
        self.notification_center = (
            NSUserNotificationCenter.defaultUserNotificationCenter()
        )
        
    def send_notification(
        self,
        title: str,
        subtitle: Optional[str] = None,
        message: str = "",
        sound: bool = False,
        image_path: Optional[str] = None
    ):
        """Send a native macOS notification"""
        try:
            # Create notification
            notification = NSUserNotification.alloc().init()
            notification.setTitle_(title)
            
            if subtitle:
                notification.setSubtitle_(subtitle)
                
            notification.setInformativeText_(message)
            
            if sound:
                notification.setSoundName_("NSUserNotificationDefaultSoundName")
                
            if image_path:
                image = NSImage.alloc().initWithContentsOfFile_(image_path)
                if image:
                    notification.setContentImage_(image)
                    
            # Deliver notification
            self.notification_center.deliverNotification_(notification)
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            
    def remove_notification(self, notification_id: str):
        """Remove a specific notification"""
        try:
            for notification in (
                self.notification_center.deliveredNotifications()
            ):
                if notification.identifier() == notification_id:
                    self.notification_center.removeDeliveredNotification_(
                        notification
                    )
                    break
        except Exception as e:
            logger.error(f"Failed to remove notification: {e}")
            
    def remove_all_notifications(self):
        """Remove all delivered notifications"""
        try:
            self.notification_center.removeAllDeliveredNotifications()
        except Exception as e:
            logger.error(f"Failed to remove notifications: {e}") 