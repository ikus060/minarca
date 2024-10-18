# Copyright (C) 2024 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Oct. 18, 2024

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import unittest
from unittest import mock
from unittest.case import skipUnless

from minarca_client.core.compat import IS_WINDOWS
from minarca_client.core.scheduler import Scheduler

_minarca_exe = 'minarca.exe' if IS_WINDOWS else 'minarca'


class TestScheduler(unittest.TestCase):
    @mock.patch('minarca_client.core.compat.get_minarca_exe', return_value=_minarca_exe)
    def test_cycle(self, unused):
        s = Scheduler()
        s.delete()
        self.assertFalse(s.exists())
        s.create()
        self.assertTrue(s.exists())
        s.delete()
        self.assertFalse(s.exists())

    @skipUnless(IS_WINDOWS, reason="feature only supported on Windows")
    @mock.patch('minarca_client.core.compat.get_minarca_exe', return_value=_minarca_exe)
    def test_schedule_job_with_credentials(self, *unused):
        # When trying to register a task with high priviledge with wrong username password
        # Then an exception is raise
        s = Scheduler()
        with self.assertRaises(OSError) as context:
            s.create(run_if_logged_out=('test', 'invalid'))

        self.assertEqual(context.exception.winerror, -2147023564)  # invalid user
