# Copyleft (C) 2024 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import os

import psutil
from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection

__all__ = ['send_notification', 'clear_notification']

# From conjob, in order to send notification to the user's dbus session,
# we need to lookup the DBUS address from other process owned by the same user.
if 'DBUS_SESSION_BUS_ADDRESS' not in os.environ:
    current_uid = os.getuid()
    for proc in psutil.process_iter(['pid', 'name', 'environ', 'uids']):
        try:
            env = proc.info['environ']
            uid = proc.info['uids'].real
            if current_uid == uid and env and 'DBUS_SESSION_BUS_ADDRESS' in env:
                os.environ['DBUS_SESSION_BUS_ADDRESS'] = env['DBUS_SESSION_BUS_ADDRESS']
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def send_notification(title, body, replace_id=None):
    assert isinstance(title, str), f"Expected 'title' to be a string, got {type(title).__name__} instead."
    assert isinstance(body, str), f"Expected 'body' to be a string, got {type(body).__name__} instead."
    assert (
        replace_id is None or isinstance(replace_id, int) or (isinstance(replace_id, str) and replace_id.isdigit())
    ), f"Expected 'replace_id' to be None, an integer, or a string containing digits, but got {type(replace_id).__name__}: {replace_id}"
    # Convert string to integer
    if isinstance(replace_id, str):
        replace_id = int(replace_id)
    # Replace None by 0
    if replace_id is None:
        replace_id = 0
    notifications = DBusAddress(
        '/org/freedesktop/Notifications',
        bus_name='org.freedesktop.Notifications',
        interface='org.freedesktop.Notifications',
    )
    connection = open_dbus_connection(bus='SESSION')
    # Construct a new D-Bus message. new_method_call takes the address, the
    # method name, the signature string, and a tuple of arguments.
    msg = new_method_call(
        notifications,
        'Notify',
        'susssasa{sv}i',
        (
            'minarca',  # App name
            replace_id,
            '',  # Icon
            title,  # Summary
            body,
            [],
            {},  # Actions, hints
            -1,  # expire_timeout (-1 = default)
        ),
    )

    # Send the message and wait for the reply
    reply = connection.send_and_get_reply(msg)
    notification_id = reply.body[0]
    connection.close()
    return notification_id


def clear_notification(notification_id):
    assert (
        notification_id is None
        or isinstance(notification_id, int)
        or (isinstance(notification_id, str) and notification_id.isdigit())
    ), f"Expected 'notification_id' to be None, an integer, or a string containing digits, but got {type(notification_id).__name__}: {notification_id}"
    # Convert string to integer
    if isinstance(notification_id, str):
        notification_id = int(notification_id)
    # Do nothing if notification is not defined
    if notification_id is None:
        return
    notifications = DBusAddress(
        '/org/freedesktop/Notifications',
        bus_name='org.freedesktop.Notifications',
        interface='org.freedesktop.Notifications',
    )
    connection = open_dbus_connection(bus='SESSION')
    # Construct a new D-Bus message. new_method_call takes the address, the
    # method name, the signature string, and a tuple of arguments.
    msg = new_method_call(
        notifications,
        'CloseNotification',
        'u',
        (notification_id,),
    )
    connection.send(msg)
