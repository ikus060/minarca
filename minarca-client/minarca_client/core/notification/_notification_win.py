# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import os
import uuid

from win11toast import clear_toast, notify

from minarca_client.locale import _

try:
    from importlib.resources import resource_filename
except ImportError:
    # For Python 2 or Python 3 with older setuptools
    from pkg_resources import resource_filename

APP_ID = 'Minarca'


def send_notification(title, body, replace_id=None):
    icon = resource_filename('minarca_client', 'ui/theme/resources/minarca.ico')
    icon_def = None
    if os.path.isfile(icon):
        icon_def = {'src': icon, 'placement': 'appLogoOverride'}

    # Generate or reuse notificaiton id as tag.
    if replace_id:
        tag = replace_id
    else:
        tag = str(uuid.uuid4())

    # This make use of "minarca://" protocol.
    buttons = [{'activationType': 'protocol', 'arguments': 'minarca://test', 'content': _('Show details')}]
    notify(title=title, body=body, icon=icon_def, app_id=APP_ID, buttons=buttons, tag=tag, group='default')
    return None


def clear_notification(notification_id):
    # On Windows, we make use of tag & groupe to clear a notification.
    clear_toast(app_id=APP_ID, tag=notification_id, group='default')
