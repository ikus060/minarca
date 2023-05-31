# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Sep. 25, 2020

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from parameterized import parameterized
from tzlocal import get_localzone

from minarca_server import shell
from minarca_server.shell import Jail

USERNAME = 'joe'
USERROOT = tempfile.gettempdir() + '/backups/joe'
OUTPUT = tempfile.gettempdir() + '/output.txt'
PY_VERSION = (sys.version_info.major, sys.version_info.minor)


class Test(unittest.TestCase):
    def setUp(self):
        unittest.TestCase.setUp(self)
        os.makedirs(USERROOT, exist_ok=True)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        shutil.rmtree(USERROOT, ignore_errors=True)
        try:
            os.remove(OUTPUT)
        except Exception:
            pass

    def test_main_without_ssh_original_command(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            with contextlib.redirect_stderr(f):
                with self.assertRaises(SystemExit):
                    os.environ['MINARCA_USERNAME'] = USERNAME
                    os.environ['MINARCA_USER_ROOT'] = USERROOT
                    try:
                        shell.main([])
                    finally:
                        del os.environ["MINARCA_USERNAME"]
                        del os.environ["MINARCA_USER_ROOT"]
        self.assertTrue('ERROR no command provided.' in f.getvalue(), msg='%s' % f.getvalue())

    def test_main_with_echo_command(self):
        with open(OUTPUT, 'wb') as f:
            with contextlib.redirect_stdout(f):
                with contextlib.redirect_stderr(f):
                    os.environ['MINARCA_USERNAME'] = USERNAME
                    os.environ['MINARCA_USER_ROOT'] = USERROOT
                    os.environ["SSH_ORIGINAL_COMMAND"] = "echo -n 1"
                    try:
                        shell.main([])
                    finally:
                        del os.environ["MINARCA_USERNAME"]
                        del os.environ["MINARCA_USER_ROOT"]
                        del os.environ["SSH_ORIGINAL_COMMAND"]
        with open(OUTPUT, 'rb') as f:
            value = f.read()
            self.assertEqual(b'1', value, "output of `echo -n 1` should be 1")

    @parameterized.expand(
        [
            ("rdiff-backup --server", None),
            ("my-computer-legacy", "1.2"),
            ("minarca/3.8.0 rdiff-backup/1.2.8 (Linux 5.11.8-051108-generic amd64)", "1.2"),
            ("minarca/4.4.0 rdiff-backup/2.0.5 (Linux 5.11.8-051108-generic amd64)", "2.0"),
            ("minarca/5.0.0 rdiff-backup/2.2.4 (Linux 5.11.8-051108-generic amd64)", "2.2"),
        ]
    )
    @mock.patch('minarca_server.shell._find_rdiff_backup', return_value='/usr/bin/rdiff-backup-test')
    @mock.patch('minarca_server.shell._jail')
    def test_main_with_user_agent(
        self,
        ssh_original_cmd,
        expect_version,
        rdiff_backup_jail_mock,
        find_rdiff_backup_mock,
    ):
        # Minarca is sending a user agent string containing the rdiff-backup
        # version.
        os.environ['MINARCA_USERNAME'] = USERNAME
        os.environ['MINARCA_USER_ROOT'] = USERROOT
        os.environ["SSH_ORIGINAL_COMMAND"] = ssh_original_cmd
        try:
            shell.main([])
        finally:
            del os.environ["MINARCA_USERNAME"]
            del os.environ["MINARCA_USER_ROOT"]
            del os.environ["SSH_ORIGINAL_COMMAND"]
        rdiff_backup_jail_mock.assert_called_once_with('/tmp/backups/joe', ['/usr/bin/rdiff-backup-test', '--server'])
        if expect_version is None:
            find_rdiff_backup_mock.assert_called_once_with()
        else:
            find_rdiff_backup_mock.assert_called_once_with(version=expect_version)

    def test_jail(self):
        # Write a file in jail folder
        with open(os.path.join(USERROOT, 'test.txt'), 'w') as f:
            f.write('coucou')
        # Run jail and print content of the file.
        shell._jail(USERROOT, ['cat', 'test.txt'])

    def test_jail_readonly_bin(self):
        # Skip this test if running as root. Because root can write everywhere
        if os.getuid() == 0:
            return
        # Try to write in /bin directory should fail.
        with Jail(USERROOT):
            with self.assertRaises(OSError):
                with open("/bin/test.yxy", 'w') as f:
                    f.write('foo')

    def test_jail_proc(self):
        with Jail(USERROOT):
            subprocess.check_call(['ps'], stdout=subprocess.PIPE)

    def test_jail_tz(self):
        tz = get_localzone().zone
        shell._jail(USERROOT, ['/bin/bash', '-c', 'echo $TZ > tz.txt'])
        with open(os.path.join(USERROOT, 'tz.txt'), 'r') as f:
            self.assertEqual(tz + '\n', f.read(), "timezone should be define in jail")
