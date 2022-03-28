# Copyright (C) 2021 IKUS Software inc. All rights reserved.
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
from unittest.case import skipIf

from minarca_client.core.compat import IS_WINDOWS
from minarca_client.core.config import Datetime, Pattern, Patterns, Settings, Status

_home = 'C:/Users' if IS_WINDOWS else '/home'


class PatternTest(unittest.TestCase):
    def test_is_wildcard(self):
        self.assertTrue(Pattern(True, '*.bak', None).is_wildcard())
        self.assertTrue(Pattern(True, '**/temp', None).is_wildcard())
        self.assertFalse(Pattern(True, '.', None).is_wildcard())
        self.assertFalse(Pattern(True, '..', None).is_wildcard())
        self.assertFalse(Pattern(True, _home, None).is_wildcard())


class PatternsTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def test_defaults(self):
        patterns = Patterns('patterns')
        self.assertEqual([], patterns)
        patterns.defaults()
        self.assertNotEqual([], patterns)

    def test_load(self):
        with open('patterns', 'w') as f:
            f.write("# comments\n")
            f.write("+somefilename.txt\n")
            f.write("# AutoCad Backup file\n")
            f.write("-*.bak\n")
        patterns = Patterns('patterns')
        self.assertEqual(Pattern(True, 'somefilename.txt', 'comments'), patterns[0])
        self.assertEqual(Pattern(False, '*.bak', 'AutoCad Backup file'), patterns[1])

    def test_load_with_missing_file(self):
        patterns = Patterns('invalid')
        self.assertEqual(0, len(patterns))

    def test_save(self):
        with open('patterns', 'w') as f:
            f.write("")
        patterns = Patterns('patterns')
        patterns.append(Pattern(True, '*.bak', 'AutoCAD Backup file'))
        patterns.append(Pattern(True, '$~*', 'Office Temporary files'))
        patterns.save()
        with open('patterns', 'r') as f:
            data = f.read()
        self.assertEqual("# AutoCAD Backup file\n+*.bak\n# Office Temporary files\n+$~*\n", data)

    @skipIf(IS_WINDOWS, 'only or unix')
    def test_group_by_roots_unix(self, *unused):
        with open('patterns', 'w') as f:
            f.write("")
        patterns = Patterns('patterns')
        patterns.append(Pattern(True, '/home/', 'User files'))
        self.assertEqual([('/', patterns)], list(patterns.group_by_roots()))

    @skipIf(not IS_WINDOWS, 'only for windows')
    @mock.patch('minarca_client.core.config.IS_WINDOWS', return_value=True)
    def test_group_by_roots_win(self, *unused):
        with open('p', 'w') as f:
            f.write("")
        p = Patterns('p')
        p.append(Pattern(True, 'C:/foo', None))
        p.append(Pattern(True, '*.bak', None))
        p.append(Pattern(True, 'C:\\bar', None))
        p.append(Pattern(True, '$~*', None))
        p.append(Pattern(True, 'D:\\bar', None))
        groups = list(p.group_by_roots())
        self.assertEqual(
            [
                (
                    'C:/',
                    [
                        Pattern(True, 'C:/foo', None),
                        Pattern(True, '*.bak', None),
                        Pattern(True, 'C:/bar', None),
                        Pattern(True, '$~*', None),
                    ],
                ),
                (
                    'D:/',
                    [
                        Pattern(True, '*.bak', None),
                        Pattern(True, '$~*', None),
                        Pattern(True, 'D:/bar', None),
                    ],
                ),
            ],
            groups,
        )

    @skipIf(not IS_WINDOWS, 'only for windows')
    @mock.patch('minarca_client.core.config.IS_WINDOWS', return_value=True)
    def test_group_by_roots_win_exclude_other_root(self, *unused):
        p = Patterns('p')
        p.append(Pattern(True, 'C:/foo', None))
        p.append(Pattern(True, '*.bak', None))
        p.append(Pattern(True, 'C:\\bar', None))
        p.append(Pattern(True, '$~*', None))
        p.append(Pattern(False, 'D:\\bar', None))
        groups = list(p.group_by_roots())
        self.assertEqual(
            [
                (
                    'C:/',
                    [
                        Pattern(True, 'C:/foo', None),
                        Pattern(True, '*.bak', None),
                        Pattern(True, 'C:/bar', None),
                        Pattern(True, '$~*', None),
                    ],
                ),
            ],
            groups,
        )


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
        self.assertEqual(None, config['username'])
        self.assertEqual(None, config['repositoryname'])
        self.assertEqual(False, config['configured'])
        self.assertEqual(24, config['schedule'])
        # Validate default value
        self.assertEqual(True, config['check_latest_version'])

    def test_load_without_check_latest_version(self):
        with open('test.properties', 'w') as f:
            f.write("username=foo\n")
            f.write("repositoryname=bar\n")
            f.write("configured=true\n")
            f.write("schedule=24\n")
        config = Settings('test.properties')
        self.assertEqual('foo', config['username'])
        self.assertEqual('bar', config['repositoryname'])
        self.assertEqual(True, config['configured'])
        self.assertEqual(24, config['schedule'])
        # Validate default value
        self.assertEqual(True, config['check_latest_version'])

    def test_load_with_check_latest_version(self):
        with open('test.properties', 'w') as f:
            f.write("username=foo\n")
            f.write("repositoryname=bar\n")
            f.write("configured=true\n")
            f.write("schedule=24\n")
            f.write("check_latest_version=False")
        config = Settings('test.properties')
        self.assertEqual(False, config['check_latest_version'])

    def test_configured(self):

        for text in ['true', 'True', '1']:
            with open('test.properties', 'w') as f:
                f.write("configured=%s\n" % text)
            config = Settings('test.properties')
            self.assertEqual(True, config['configured'])

        for text in ['False', 'false', '0']:
            with open('test.properties', 'w') as f:
                f.write("configured=%s\n" % text)
            config = Settings('test.properties')
            self.assertEqual(False, config['configured'])

    def test_load_with_missing_file(self):
        config = Settings('invalid.properties')
        self.assertEqual(Settings._DEFAULT, config)

    def test_save(self):
        with open('test.properties', 'w') as f:
            f.write("\n")
        config = Settings('test.properties')
        config['username'] = 'foo'
        config['repositoryname'] = 'bar'
        config.save()
        with open('test.properties', 'r') as f:
            data = f.read()
        self.assertTrue("username=foo" in data)
        self.assertTrue("repositoryname=bar" in data)


class StatusTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def test_load(self):
        with open('status.properties', 'w') as f:
            f.write("details=nothing to backup, make sure you have at least one valid include patterns\n")
            f.write("lastdate=1623094810348\n")
            f.write("lastresult=FAILURE\n")
            f.write("lastsuccess=1622832320569\n")
        status = Status('status.properties')
        self.assertEqual('nothing to backup, make sure you have at least one valid include patterns', status['details'])
        self.assertEqual(Datetime(1623094810348), status['lastdate'])
        self.assertEqual('FAILURE', status['lastresult'])
        self.assertEqual(Datetime(1622832320569), status['lastsuccess'])

    def test_load_with_missing_file(self):
        status = Status('invalid.properties')
        self.assertEqual(Status._DEFAULT, status)

    def test_save(self):
        with open('status.properties', 'w') as f:
            f.write("\n")
        status = Status('status.properties')
        status['lastresult'] = 'SUCCESS'
        status['lastsuccess'] = Datetime(1622832320000)
        status.save()
        with open('status.properties', 'r') as f:
            data = f.read()
        self.assertTrue("lastresult=SUCCESS" in data)
        self.assertTrue("lastsuccess=1622832320000" in data)
        self.assertTrue("lastdate=" not in data)
        self.assertTrue("details=" not in data)
