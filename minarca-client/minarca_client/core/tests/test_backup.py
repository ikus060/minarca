# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import os
import tempfile
import unittest
from unittest import mock
from unittest.case import skipUnless
from unittest.mock import MagicMock

from minarca_client.core import Backup, BackupInstance, limit
from minarca_client.core.compat import IS_WINDOWS


class TestBackup(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        os.environ['MINARCA_CONFIG_HOME'] = self.tmp.name
        os.environ['MINARCA_DATA_HOME'] = self.tmp.name
        self.backup = Backup()
        self.backup.scheduler = MagicMock()

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()
        del os.environ['MINARCA_CONFIG_HOME']
        del os.environ['MINARCA_DATA_HOME']

    def test_getitem_single(self):
        # Given a single minarca.properties
        with open(os.path.join(self.tmp.name, 'minarca.properties'), 'w') as f:
            f.write('')
        # Then a single instance is return by Backup()
        self.assertEqual(1, len(self.backup))
        self.assertIsNotNone(BackupInstance(''), self.backup[0])
        self.assertEqual([BackupInstance('')], list(self.backup))

    def test_getitem_multiple(self):
        # Given a single minarca.properties
        with open(os.path.join(self.tmp.name, 'minarca.properties'), 'w') as f:
            f.write('')
        # Given a single minarca.properties
        with open(os.path.join(self.tmp.name, 'minarca1.properties'), 'w') as f:
            f.write('')
        # Then a single instance is return by Backup()
        self.assertEqual(2, len(self.backup))
        self.assertIsNotNone(BackupInstance(''), self.backup[0])
        self.assertIsNotNone(BackupInstance('1'), self.backup[1])
        self.assertEqual([BackupInstance(''), BackupInstance('1')], list(self.backup))

    def test_getitem_limit(self):
        # Given a single minarca.properties
        with open(os.path.join(self.tmp.name, 'minarca.properties'), 'w') as f:
            f.write('')
        # Given a single minarca.properties
        with open(os.path.join(self.tmp.name, 'minarca1.properties'), 'w') as f:
            f.write('')
        # With limit(None)
        # Then all instances are returned
        self.assertEqual(2, len(self.backup[limit(None)]))
        # With limit(0)
        # Then first instance is returned
        self.assertEqual([BackupInstance('')], self.backup[limit('')])
        # With limit(1)
        # Then second instances is returned
        self.assertEqual([BackupInstance('1')], self.backup[limit('1')])

    @mock.patch('minarca_client.core.compat.get_minarca_exe', return_value='minarca.exe' if IS_WINDOWS else 'minarca')
    def test_schedule_job(self, *unused):
        self.backup.schedule_job()
        self.assertTrue(self.backup.scheduler.exists())

    @skipUnless(IS_WINDOWS, reason="feature only supported on Windows")
    @mock.patch('minarca_client.core.compat.get_minarca_exe', return_value='minarca.exe' if IS_WINDOWS else 'minarca')
    def test_schedule_job_with_credentials(self, *unused):
        # When scheduling a job with credentials
        self.backup.schedule_job(run_if_logged_out=('test', 'invalid'))
        # Then scheduler is called with credentials
        self.backup.scheduler.create.assert_called_once_with(run_if_logged_out=('test', 'invalid'))
