# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 10, 2024

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import os
import unittest

from minarca_client.core.compat import IS_LINUX
from minarca_client.core.notification import clear_notification, send_notification

NO_DBUS = not os.environ.get('DBUS_SESSION_BUS_ADDRESS', False)


@unittest.skipIf(IS_LINUX and NO_DBUS, 'On Linux, D-Bus is required for this test')
class TestNotification(unittest.TestCase):

    def test_send_and_clear_notification(self):
        notification_id = send_notification('Some title', 'Some Body', replace_id=None)
        self.assertIsNotNone(notification_id)
        clear_notification(notification_id)

    def test_replace_notification(self):
        notification_id = send_notification('Some title', 'Some Body', replace_id=None)
        self.assertIsNotNone(notification_id)
        return_id = send_notification('Some title', 'Some Body', replace_id=notification_id)
        self.assertEqual(notification_id, return_id)
        clear_notification(notification_id)
