# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from minarca_client.core import compat
from minarca_client.core.compat import (IS_LINUX, IS_MAC, IS_WINDOWS, Scheduler,
                                        ssh_keygen)
from minarca_client.tests.test import MATCH
from unittest import mock
from unittest.case import skipUnless
import os
import subprocess
import tempfile
import unittest

_echo_rdiff_backup_version = ['cmd.exe', '/c', 'echo',
                              'rdiff-backup 2.0.5'] if IS_WINDOWS else ['echo', 'rdiff-backup 2.0.5']

_original_subprocess_check_output = subprocess.check_output
_minarca_exe = 'minarca.exe' if IS_WINDOWS else 'minarca'


def mock_subprocess_check_output(*args, **kwargs):
    return _original_subprocess_check_output(_echo_rdiff_backup_version, **kwargs)


class TestCompat(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    @mock.patch('subprocess.check_output', side_effect=mock_subprocess_check_output)
    def test_get_user_agent(self, *unused):
        self.assertEqual(
            MATCH("minarca/* rdiff-backup/2.0.5 (*)"), compat.get_user_agent())

    @mock.patch('subprocess.check_output', side_effect=mock_subprocess_check_output)
    def test_get_rdiff_backup_version(self, *unused):
        self.assertEqual("2.0.5", compat.get_rdiff_backup_version())

    def test_ssh_keygen(self):
        ssh_keygen('public.key', 'private.key')
        self.assertTrue(os.path.exists('public.key'))
        self.assertTrue(os.path.exists('private.key'))
        # public should start with ssh-rsa
        with open('public.key') as f:
            self.assertTrue(f.read().startswith("ssh-rsa "))
        with open('private.key') as f:
            self.assertEqual(MATCH('-----BEGIN * PRIVATE KEY-----*'), f.read())


@skipUnless(IS_LINUX, 'Only for Unix')
@mock.patch('minarca_client.core.compat.get_home', return_value='/home/username')
class TestCompatLinux(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def test_get_config_home(self, *unused):
        self.assertEqual('/home/username/.config/minarca',
                         compat.get_config_home(False))

    def test_get_data_home(self, *unused):
        self.assertEqual('/home/username/.local/share/minarca',
                         compat.get_data_home(False))

    def test_get_log_file(self, *unused):
        self.assertEqual('/home/username/.local/share/minarca/minarca.log',
                         compat.get_log_file(False))

    def test_get_ssh(self, *unused):
        self.assertTrue(compat.get_ssh().endswith('ssh'))


@skipUnless(IS_MAC, 'Only for MacOS')
@mock.patch('minarca_client.core.compat.get_home', return_value='/Users/username')
class TestCompatMacos(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def test_get_config_home(self, *unused):
        self.assertEqual('/Users/username/Library/Preferences/Minarca',
                         compat.get_config_home(False))

    def test_get_data_home(self, *unused):
        self.assertEqual('/Users/username/Library/Minarca',
                         compat.get_data_home(False))

    def test_get_log_file(self, *unused):
        self.assertEqual('/Users/username/Library/Logs/Minarca/minarca.log',
                         compat.get_log_file(False))

    def test_get_ssh(self, *unused):
        self.assertTrue(compat.get_ssh().endswith('ssh'))


@skipUnless(IS_WINDOWS, 'Only for Windows')
@mock.patch('minarca_client.core.compat.get_home', return_value='C:\\Users\\username')
class TestCompatWindows(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        if os.environ.get('LOCALAPPDATA'):
            del os.environ['LOCALAPPDATA']

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def test_get_config_home(self, *unused):
        self.assertEqual('C:\\Users\\username\\AppData\\Local\\minarca',
                         compat.get_config_home(False))

    def test_get_data_home(self, *unused):
        self.assertEqual('C:\\Users\\username\\AppData\\Local\\minarca',
                         compat.get_data_home(False))

    def test_get_log_file(self, *unused):
        self.assertEqual('C:\\Users\\username\\AppData\\Local\\minarca\\minarca.log',
                         compat.get_log_file(False))

    def test_get_ssh(self, *unused):
        self.assertTrue(compat.get_ssh().endswith('ssh.exe'))


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