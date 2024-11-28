from Foundation import NSUserNotificationCenter, NSUserNotification
import objc
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class NotificationManager:
    """Manage macOS notifications"""
    
    def __init__(self):
        self.center = NSUserNotificationCenter.defaultUserNotificationCenter()
        
    def send_notification(self, title: str, message: str, 
                         subtitle: Optional[str] = None,
                         sound: bool = True,
                         action_button: Optional[str] = None,
                         delay: Optional[int] = None):
        """Send macOS notification"""
        notification = NSUserNotification.alloc().init()
        notification.setTitle_(title)
        notification.setInformativeText_(message)
        
        if subtitle:
            notification.setSubtitle_(subtitle)
            
        if sound:
            notification.setSoundName_("NSUserNotificationDefaultSoundName")
            
        if action_button:
            notification.setActionButtonTitle_(action_button)
            
        if delay:
            delivery_date = NSDate.dateWithTimeIntervalSinceNow_(delay)
            notification.setDeliveryDate_(delivery_date)
            
        self.center.scheduleNotification_(notification)
        
    def get_notifications(self) -> List[Dict]:
        """Get pending notifications"""
        notifications = []
        for notification in self.center.scheduledNotifications():
            notifications.append({
                'title': notification.title(),
                'message': notification.informativeText(),
                'subtitle': notification.subtitle(),
                'delivery_date': notification.deliveryDate(),
                'action_button': notification.actionButtonTitle()
            })
        return notifications
        
    def clear_notifications(self, older_than: Optional[timedelta] = None):
        """Clear notifications"""
        if older_than:
            cutoff = datetime.now() - older_than
            for notification in self.center.scheduledNotifications():
                if notification.deliveryDate() < cutoff:
                    self.center.removeScheduledNotification_(notification)
        else:
            self.center.removeAllDeliveredNotifications() 