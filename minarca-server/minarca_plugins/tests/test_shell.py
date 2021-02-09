'''
Created on Sep. 25, 2020

@author: Patrik Dufresne
'''
import contextlib
import io
import os
import shutil
from stat import ST_MODE
import sys
import tempfile
from unittest import mock
import unittest

from minarca_plugins import shell
from minarca_plugins.shell import Jail
import subprocess

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

    def test_parse_args(self):
        args = shell._parse_args([USERNAME, USERROOT])
        self.assertEqual(args.username, USERNAME)
        self.assertEqual(args.userroot, USERROOT)

    def test_parse_args_with_missing_arguments(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            with contextlib.redirect_stderr(f):
                with self.assertRaises(SystemExit):
                    shell._parse_args(['joe'])
        self.assertTrue('the following arguments are required' in f.getvalue(), msg='%s' % f.getvalue())

    def test_main_without_ssh_original_command(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            with contextlib.redirect_stderr(f):
                with self.assertRaises(SystemExit):
                    shell.main([USERNAME, USERROOT])
        self.assertTrue('ERROR no command provided.' in f.getvalue(), msg='%s' % f.getvalue())

    def test_main_with_echo_command(self):
        with open(OUTPUT, 'wb') as f:
            with contextlib.redirect_stdout(f):
                with contextlib.redirect_stderr(f):
                    os.environ["SSH_ORIGINAL_COMMAND"] = "echo -n 1"
                    try:
                        shell.main([USERNAME, USERROOT])
                    finally:
                        del os.environ["SSH_ORIGINAL_COMMAND"]
        with open(OUTPUT, 'rb') as f:
            value = f.read()
            self.assertEqual(b'1', value, "output of `echo -n 1` should be 1")

    @mock.patch('minarca_plugins.shell._jail')
    def test_main_with_rdiff_backup_server(self, rdiff_backup_jail_mock):
        os.environ["SSH_ORIGINAL_COMMAND"] = "rdiff-backup --server"
        try:
            shell.main([USERNAME, USERROOT])
        finally:
            del os.environ["SSH_ORIGINAL_COMMAND"]
        rdiff_backup_jail_mock.assert_called_once_with('/tmp/backups/joe', ['rdiff-backup', '--server'])

    @mock.patch('minarca_plugins.shell._jail')
    def test_main_with_minarca_repo(self, rdiff_backup_jail_mock):
        os.environ["SSH_ORIGINAL_COMMAND"] = "my-computer"
        try:
            shell.main([USERNAME, USERROOT])
        finally:
            del os.environ["SSH_ORIGINAL_COMMAND"]
        rdiff_backup_jail_mock.assert_called_once_with('/tmp/backups/joe', ['rdiff-backup', '--server'])

    def test_jail(self):
        # Write a file in jail folder
        with open(os.path.join(USERROOT, 'test.txt'), 'w') as f:
            f.write('coucou')
        # Run jail and print content of the file.
        with open(OUTPUT, 'wb') as f:
            with contextlib.redirect_stdout(f):
                with contextlib.redirect_stderr(f):
                    shell._jail(USERROOT, ['cat', 'test.txt'])
        # Validate the file output.
        with open(OUTPUT, 'rb') as f:
            value = f.read()
            if PY_VERSION < (3, 6):
                # On debian stretch, we use an old snakeoil package, that miss behave when tested.
                self.assertEqual(b'coucoucoucou', value, "output of `echo coucou` should be `coucou`")
            else:
                self.assertEqual(b'coucou', value, "content of `test.txt` should be `coucou`")

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
        # Try to write in /bin directory should fail.
        with Jail(USERROOT):
            subprocess.check_call(['ps', '-ef'])


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
