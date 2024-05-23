# Copyleft (C) 2024 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import os

import psutil
from jeepney import DBusAddress, new_method_call
from jeepney.io.blocking import open_dbus_connection

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
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass


def send_notification(title, body, replace_id=None):
    assert isinstance(title, str)
    assert isinstance(body, str)
    assert replace_id is None or isinstance(replace_id, int) or (isinstance(replace_id, str) and replace_id.isdigit())
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
            'jeepney_test',  # App name
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
    pass
