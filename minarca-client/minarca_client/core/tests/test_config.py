# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import datetime
import os
import tempfile
import time
import unittest
from unittest.case import skipIf

from minarca_client.core.compat import IS_WINDOWS
from minarca_client.core.config import Datetime
from minarca_client.core.settings import Settings
from minarca_client.core.status import Status


class SettingsTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def test_load_without_file(self):
        config = Settings('test.properties')
        self.assertEqual(None, config.username)
        self.assertEqual(None, config.repositoryname)
        self.assertEqual(False, config.configured)
        self.assertEqual(24, config.schedule)
        # Validate default value
        self.assertEqual(True, config.check_latest_version)

    def test_load_without_check_latest_version(self):
        with open('test.properties', 'w') as f:
            f.write("username=foo\n")
            f.write("repositoryname=bar\n")
            f.write("configured=true\n")
            f.write("schedule=24\n")
        config = Settings('test.properties')
        self.assertEqual('foo', config.username)
        self.assertEqual('bar', config.repositoryname)
        self.assertEqual(True, config.configured)
        self.assertEqual(24, config.schedule)
        # Validate default value
        self.assertEqual(True, config.check_latest_version)

    def test_load_with_check_latest_version(self):
        with open('test.properties', 'w') as f:
            f.write("username=foo\n")
            f.write("repositoryname=bar\n")
            f.write("configured=true\n")
            f.write("schedule=24\n")
            f.write("check_latest_version=False")
        config = Settings('test.properties')
        self.assertEqual(False, config.check_latest_version)

    def test_configured(self):
        for text in ['true', 'True', '1']:
            with open('test.properties', 'w') as f:
                f.write("configured=%s\n" % text)
            config = Settings('test.properties')
            self.assertEqual(True, config.configured)

        for text in ['False', 'false', '0']:
            with open('test.properties', 'w') as f:
                f.write("configured=%s\n" % text)
            config = Settings('test.properties')
            self.assertEqual(False, config.configured)

    def test_save(self):
        with open('test.properties', 'w') as f:
            f.write("\n")
        config = Settings('test.properties')
        config.username = 'foo'
        config.repositoryname = 'bar'
        config.save()
        with open('test.properties', 'r') as f:
            data = f.read()
        self.assertTrue("username=foo" in data)
        self.assertTrue("repositoryname=bar" in data)

    def test_transaction(self):
        # Given a config file
        with open('test.properties', 'w') as f:
            f.write("\n")
        config = Settings('test.properties')
        # When starting a transaction
        with config as c:
            c.username = 'foo'
            c.repositoryname = 'bar'
            # Then within transaction, changes are not saved
            with open('test.properties', 'r') as f:
                data = f.read()
            self.assertEqual('\n', data)
        # Then after transaction, changes are saved
        with open('test.properties', 'r') as f:
            data = f.read()
        self.assertTrue("username=foo" in data)
        self.assertTrue("repositoryname=bar" in data)

    def test_set_value_invalid(self):
        # Given a config file
        config = Settings('test.properties')
        # When trying to set an invalid value type
        # Then an exception is raised
        with self.assertRaises(ValueError):
            config.schedule = 'invalid'
        # When trying to set the wrong type
        config.schedule = '4321'
        # Then value is coerse
        self.assertEqual(4321, config.schedule)

    def test_pause_until(self):
        # Given an empty status file
        config = Settings('test.properties')
        # Then pause_until is None
        self.assertIsNone(config.pause_until)
        # When setting value
        now = Datetime()
        config.pause_until = now
        # Then value get updated
        self.assertEqual(now, config.pause_until)
        # When pause_until is set to None
        config.pause_until = None
        # Then value is None
        self.assertIsNone(config.pause_until)


class StatusTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def test_load_without_file(self):
        # Given an invalid invalid.
        status = Status('invalid.properties')
        # Then default value are used
        self.assertEqual(None, status.details)
        self.assertEqual(None, status.lastdate)
        self.assertEqual('UNKNOWN', status.lastresult)
        self.assertEqual(None, status.pid)
        self.assertEqual(None, status.action)

    def test_load(self):
        with open('status.properties', 'w') as f:
            f.write("details=nothing to backup, make sure you have at least one valid include patterns\n")
            f.write("lastdate=1623094810348\n")
            f.write("lastresult=FAILURE\n")
            f.write("lastsuccess=1622832320569\n")
        status = Status('status.properties')
        self.assertEqual('nothing to backup, make sure you have at least one valid include patterns', status.details)
        self.assertEqual(Datetime(1623094810348), status.lastdate)
        self.assertEqual('FAILURE', status.lastresult)
        self.assertEqual(Datetime(1622832320569), status.lastsuccess)

    def test_save(self):
        with open('status.properties', 'w') as f:
            f.write("\n")
        status = Status('status.properties')
        status.lastresult = 'SUCCESS'
        status.lastsuccess = Datetime(1622832320000)
        status.save()
        with open('status.properties', 'r') as f:
            data = f.read()
        self.assertTrue("lastresult=SUCCESS" in data)
        self.assertTrue("lastsuccess=1622832320000" in data)
        self.assertTrue("lastdate=" not in data)
        self.assertTrue("details=" not in data)

    def test_transaction(self):
        # Given a status
        status = Status('status.properties')
        self.assertNotEqual('RUNNING', status.current_status)
        with status as t:
            t.pid = os.getpid()
            t.lastresult = 'RUNNING'
            t.lastdate = Datetime()
            t.details = ''
            t.action = 'backup'
        with status as t:
            t.lastresult = 'SUCCESS'
            self.assertEqual('SUCCESS', status.lastresult)
            t.lastsuccess = Datetime()
            t.lastdate = status.lastsuccess
            t.details = ''
        self.assertEqual('SUCCESS', status.lastresult)


class DatetimeTest(unittest.TestCase):
    def test_add(self):
        self.assertEqual(Datetime(1688580806000) + datetime.timedelta(hours=24), Datetime(1688667206000))

    def test_sub(self):
        self.assertEqual(Datetime(1688580806000) - datetime.timedelta(hours=24), Datetime(1688494406000))

    @skipIf(IS_WINDOWS, 'time.tzset not available on Windows')
    def test_strftime(self):
        old_tz = os.environ.get('TZ')
        try:
            os.environ['TZ'] = 'UTC'
            time.tzset()
            self.assertEqual("2023-10-24 12:14", Datetime(1698149641123).strftime("%Y-%m-%d %H:%M"))
        finally:
            if old_tz is None:
                del os.environ['TZ']
            else:
                os.environ['TZ'] = old_tz
            time.tzset()
