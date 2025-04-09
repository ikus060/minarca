# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import sys

IS_WINDOWS = sys.platform in ['win32']
IS_LINUX = sys.platform in ['linux', 'linux2']
IS_MAC = sys.platform == 'darwin'

if IS_WINDOWS:
    from ._notification_win import *  # noqa
elif IS_LINUX:
    from ._notification_dbus import *  # noqa
elif IS_MAC:
    from ._notification_cocoa import *  # noqa
else:

    def send_notification(title, body, replace_id=None):
        # No-op implementation
        pass

    def clear_notification(notification_id):
        # No-op implementation
        pass
