# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import uuid

import objc  # noqa
from Foundation import NSUserNotification, NSUserNotificationCenter

__all__ = ['send_notification', 'clear_notification']


def send_notification(title, body, replace_id=None):
    assert replace_id is None or isinstance(replace_id, str)
    # icon is not supported on cocoa. Application icon is used by default.

    # Create a new notification
    notification = NSUserNotification.alloc().init()
    # Set the title, subtitle, and informative text of the notification
    notification.setTitle_(title)
    notification.setInformativeText_(body)

    # Generate a uuid if not provided
    if replace_id:
        notification.setIdentifier_(replace_id)
    else:
        notification.setIdentifier_(str(uuid.uuid4()))

    # Get the default notification center
    center = NSUserNotificationCenter.defaultUserNotificationCenter()

    # Deliver the notification
    center.deliverNotification_(notification)

    return notification.identifier()


def clear_notification(notification_id):
    assert isinstance(notification_id, str)
    # Get the default notification center
    center = NSUserNotificationCenter.defaultUserNotificationCenter()

    # Loop on notification and clear matching identifier
    for n in center.deliveredNotifications():
        if n.identifier() == notification_id:
            center.removeDeliveredNotification_(n)
            break
