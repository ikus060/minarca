'''
Created on Sep. 25, 2020

@author: Patrik Dufresne
'''
import contextlib
import io
import os
import shutil
import tempfile
import unittest

from mock import MagicMock

from minarca_plugins import shell

USERNAME = 'joe'
USERROOT = tempfile.gettempdir() + '/backups/joe'
OUTPUT = tempfile.gettempdir() + '/output.txt'


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

    def test_main_with_rdiff_backup_server(self):
        shell._exec = MagicMock()
        os.environ["SSH_ORIGINAL_COMMAND"] = "rdiff-backup --server"
        try:
            shell.main([USERNAME, USERROOT])
        finally:
            del os.environ["SSH_ORIGINAL_COMMAND"]
        shell._exec.assert_called_once_with(
            cmd=['rdiff-backup', '--server'],
            cwd='/tmp/backups/joe')

    def test_main_with_minarca_repo(self):
        shell._exec = MagicMock()
        os.environ["SSH_ORIGINAL_COMMAND"] = "my-computer"
        try:
            shell.main([USERNAME, USERROOT])
        finally:
            del os.environ["SSH_ORIGINAL_COMMAND"]
        shell._exec.assert_called_once_with(
            cmd=['rdiff-backup', '--server', '--restrict=my-computer'],
            cwd='/tmp/backups/joe',
        )


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
