'''
Created on Sep. 25, 2020

@author: Patrik Dufresne
'''
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
from unittest import mock
import unittest

from minarca_plugins import shell
from minarca_plugins.shell import Jail

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
        except:
            pass

    def test_main_without_ssh_original_command(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            with contextlib.redirect_stderr(f):
                with self.assertRaises(SystemExit):
                    os.environ['MINARCA_USERNAME'] = USERNAME
                    os.environ['MINARCA_USER_ROOT'] = USERROOT
                    try:
                        shell.main()
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
                        shell.main()
                    finally:
                        del os.environ["MINARCA_USERNAME"]
                        del os.environ["MINARCA_USER_ROOT"]
                        del os.environ["SSH_ORIGINAL_COMMAND"]
        with open(OUTPUT, 'rb') as f:
            value = f.read()
            self.assertEqual(b'1', value, "output of `echo -n 1` should be 1")

    @mock.patch('minarca_plugins.shell._find_rdiff_backup', return_value='/usr/bin/rdiff-backup')
    @mock.patch('minarca_plugins.shell._jail')
    def test_main_with_rdiff_backup_server(self, rdiff_backup_jail_mock, find_rdiff_backup_mock):
        os.environ['MINARCA_USERNAME'] = USERNAME
        os.environ['MINARCA_USER_ROOT'] = USERROOT
        os.environ["SSH_ORIGINAL_COMMAND"] = "rdiff-backup --server"
        try:
            shell.main()
        finally:
            del os.environ["MINARCA_USERNAME"]
            del os.environ["MINARCA_USER_ROOT"]
            del os.environ["SSH_ORIGINAL_COMMAND"]
        rdiff_backup_jail_mock.assert_called_once_with('/tmp/backups/joe', ['/usr/bin/rdiff-backup', '--server'])

    @mock.patch('minarca_plugins.shell._find_rdiff_backup', return_value='/usr/bin/rdiff-backup')
    @mock.patch('minarca_plugins.shell._jail')
    def test_main_with_minarca_legacy(self, rdiff_backup_jail_mock, find_rdiff_backup_mock):
        # First minarca version send only the repository name as the command
        # line without anymore information.
        os.environ['MINARCA_USERNAME'] = USERNAME
        os.environ['MINARCA_USER_ROOT'] = USERROOT
        os.environ["SSH_ORIGINAL_COMMAND"] = "my-computer"
        try:
            shell.main()
        finally:
            del os.environ["MINARCA_USERNAME"]
            del os.environ["MINARCA_USER_ROOT"]
            del os.environ["SSH_ORIGINAL_COMMAND"]
        rdiff_backup_jail_mock.assert_called_once_with('/tmp/backups/joe', ['/usr/bin/rdiff-backup', '--server'])
        find_rdiff_backup_mock.assert_called_once_with(version=1)

    @mock.patch('minarca_plugins.shell._find_rdiff_backup', return_value='/usr/bin/rdiff-backup')
    @mock.patch('minarca_plugins.shell._jail')
    def test_main_with_minarca_with_128(self, rdiff_backup_jail_mock, find_rdiff_backup_mock):
        # Minarca is sending a user agent string containing the rdiff-backup version.
        os.environ['MINARCA_USERNAME'] = USERNAME
        os.environ['MINARCA_USER_ROOT'] = USERROOT
        os.environ["SSH_ORIGINAL_COMMAND"] = "minarca/3.8.0 rdiff-backup/1.2.8 (Linux 5.11.8-051108-generic amd64)"
        try:
            shell.main()
        finally:
            del os.environ["MINARCA_USERNAME"]
            del os.environ["MINARCA_USER_ROOT"]
            del os.environ["SSH_ORIGINAL_COMMAND"]
        rdiff_backup_jail_mock.assert_called_once_with('/tmp/backups/joe', ['/usr/bin/rdiff-backup', '--server'])
        find_rdiff_backup_mock.assert_called_once_with(version=1)

    @mock.patch('minarca_plugins.shell._find_rdiff_backup', return_value='/usr/bin/rdiff-backup')
    @mock.patch('minarca_plugins.shell._jail')
    def test_main_with_minarca_with_205(self, rdiff_backup_jail_mock, find_rdiff_backup_mock):
        # Minarca is sending a user agent string containing the rdiff-backup version.
        os.environ['MINARCA_USERNAME'] = USERNAME
        os.environ['MINARCA_USER_ROOT'] = USERROOT
        os.environ["SSH_ORIGINAL_COMMAND"] = "minarca/3.8.0 rdiff-backup/2.0.5 (Linux 5.11.8-051108-generic amd64)"
        try:
            shell.main()
        finally:
            del os.environ["MINARCA_USERNAME"]
            del os.environ["MINARCA_USER_ROOT"]
            del os.environ["SSH_ORIGINAL_COMMAND"]
        rdiff_backup_jail_mock.assert_called_once_with('/tmp/backups/joe', ['/usr/bin/rdiff-backup', '--server'])
        find_rdiff_backup_mock.assert_called_once_with(version=2)

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


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
