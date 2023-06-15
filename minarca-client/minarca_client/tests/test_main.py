# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 9, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import contextlib
import io
import logging
import os
import tempfile
import unittest
from unittest import mock

from minarca_client import main
from minarca_client.core import Backup, HttpAuthenticationError
from minarca_client.core.compat import IS_WINDOWS
from minarca_client.core.config import Pattern, Patterns, Settings
from minarca_client.main import _EXIT_LINK_ERROR, _backup, _pattern, _schedule, _start, _status, _stop, _unlink


class TestMainParseArgs(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        os.environ['MINARCA_CONFIG_HOME'] = self.tmp.name

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()
        del os.environ['MINARCA_CONFIG_HOME']

    @mock.patch('minarca_client.main._backup')
    def test_args_backup(self, mock_backup):
        main.main(['backup'])
        mock_backup.assert_called_once_with(force=False)

    @mock.patch('minarca_client.main._backup')
    def test_args_backup_force(self, mock_backup):
        main.main(['backup', '--force'])
        mock_backup.assert_called_once_with(force=True)

    @mock.patch('minarca_client.main._pattern')
    def test_args_exclude(self, mock_pattern):
        main.main(['exclude', '*.bak'])
        mock_pattern.assert_called_once_with(include=False, pattern=['*.bak'])

    @mock.patch('minarca_client.main._pattern')
    def test_args_exclude_multiple(self, mock_pattern):
        main.main(['exclude', '*.bak', '$~*', '/proc'])
        mock_pattern.assert_called_once_with(include=False, pattern=['*.bak', '$~*', '/proc'])

    @mock.patch('minarca_client.main._pattern')
    def test_args_include(self, mock_pattern):
        main.main(['include', '*.bak'])
        mock_pattern.assert_called_once_with(include=True, pattern=['*.bak'])

    @mock.patch('minarca_client.main._pattern')
    def test_args_include_multiple(self, mock_pattern):
        main.main(['include', '*.bak', '$~*', '/proc'])
        mock_pattern.assert_called_once_with(include=True, pattern=['*.bak', '$~*', '/proc'])

    @mock.patch('minarca_client.main._link')
    def test_args_link(self, mock_link):
        main.main(
            ['link', '--remoteurl', 'https://localhost', '--username', 'foo', '--password', 'bar', '--name', 'repo']
        )
        mock_link.assert_called_once_with(
            remoteurl='https://localhost', username='foo', password='bar', name='repo', force=False
        )

    @mock.patch('minarca_client.main.Backup')
    def test_args_debug(self, mock_backup):
        main.main(['-d', 'stop'])
        self.assertEqual(logging.DEBUG, logging.getLogger().level)

    def test_args_none(self):
        with self.assertRaises(SystemExit):
            main.main([''])

    @mock.patch('minarca_client.main._ui')
    def test_args_ui(self, mock_ui):
        main.main(['ui'])
        mock_ui.assert_called_once()

    @mock.patch('minarca_client.main.SetupDialog')
    def test_args_ui_is_not_linked(self, mock_setup_dlg):
        main.main(['ui'])
        mock_setup_dlg.assert_called_once()
        mock_setup_dlg.return_value.mainloop.assert_called_once()

    @mock.patch('minarca_client.main.SetupDialog')
    @mock.patch('minarca_client.main.HomeDialog')
    def test_args_ui_is_linked(self, mock_setup_dlg, mock_home_dlg):
        main.main(['ui'])
        mock_setup_dlg.assert_not_called()
        mock_home_dlg.assert_called_once()
        mock_home_dlg.return_value.mainloop.assert_called_once()

    @mock.patch('minarca_client.main.Backup')
    def test_link(self, mock_backup):
        mock_backup.return_value.is_linked.return_value = False
        main.main(
            ['link', '--remoteurl', 'https://localhost', '--username', 'foo', '--password', 'bar', '--name', 'repo']
        )
        mock_backup.return_value.link.assert_called_once_with(
            remoteurl='https://localhost', username='foo', password='bar', repository_name='repo', force=False
        )

    @mock.patch('getpass.getpass')
    @mock.patch('minarca_client.main.Backup')
    def test_link_prompt_password(self, mock_backup, mock_getpass):
        mock_backup.return_value.is_linked.return_value = False
        mock_getpass.return_value = 'bar'
        main.main(['link', '--remoteurl', 'https://localhost', '--username', 'foo', '--name', 'repo'])
        mock_backup.return_value.link.assert_called_once_with(
            remoteurl='https://localhost', username='foo', password='bar', repository_name='repo', force=False
        )

    @mock.patch('getpass.getpass')
    @mock.patch('minarca_client.main.Backup')
    def test_link_prompt_password_null(self, mock_backup, mock_getpass):
        mock_backup.return_value.is_linked.return_value = False
        mock_getpass.return_value = ''
        with self.assertRaises(SystemExit):
            main.main(['link', '--remoteurl', 'https://localhost', '--username', 'foo', '--name', 'repo'])

    @mock.patch('getpass.getpass')
    @mock.patch('minarca_client.main.Backup')
    def test_link_wrong_password(self, mock_backup, mock_getpass):
        # Given a computer that is not configured
        mock_backup.return_value.is_linked.return_value = False
        # Given a wrong password
        mock_getpass.return_value = 'invalid'
        mock_backup.return_value.link.side_effect = HttpAuthenticationError
        # When trying to link the computer with CLI
        # Then an exception is raised
        with self.assertRaises(SystemExit) as context:
            main.main(['link', '--remoteurl', 'https://localhost', '--username', 'foo', '--name', 'repo'])
        self.assertEqual(_EXIT_LINK_ERROR, context.exception.code)

    @mock.patch('minarca_client.main._link')
    def test_args_link_force(self, mock_link):
        main.main(
            [
                'link',
                '--remoteurl',
                'https://localhost',
                '--username',
                'foo',
                '--password',
                'bar',
                '--name',
                'repo',
                '--force',
            ]
        )
        mock_link.assert_called_once_with(
            remoteurl='https://localhost', username='foo', password='bar', name='repo', force=True
        )

    @mock.patch('minarca_client.main._link')
    def test_args_link_arg_missing(self, unused_mock_link):
        with self.assertRaises(SystemExit):
            main.main(['link', '--remoteurl', 'https://localhost', '--username', 'foo', '--password', 'bar'])

    @mock.patch('minarca_client.main._patterns')
    def test_args_patterns(self, mock_patterns):
        main.main(['patterns'])
        mock_patterns.assert_called_once_with()

    @mock.patch('minarca_client.main._stop')
    def test_args_stop(self, mock_stop):
        main.main(['stop'])
        mock_stop.assert_called_once_with(force=False)

    @mock.patch('minarca_client.main._stop')
    def test_args_stop_force(self, mock_stop):
        main.main(['stop', '--force'])
        mock_stop.assert_called_once_with(force=True)

    @mock.patch('minarca_client.main._schedule')
    def test_args_schedule(self, mock_schedule):
        main.main(['schedule'])
        if IS_WINDOWS:
            mock_schedule.assert_called_once_with(schedule=Settings.DAILY, username=None, password=None)
        else:
            mock_schedule.assert_called_once_with(schedule=Settings.DAILY)

    @mock.patch('minarca_client.main._schedule')
    def test_args_schedule_daily(self, mock_schedule):
        main.main(['schedule', '--daily'])
        if IS_WINDOWS:
            mock_schedule.assert_called_once_with(schedule=Settings.DAILY, username=None, password=None)
        else:
            mock_schedule.assert_called_once_with(schedule=Settings.DAILY)

    @mock.patch('minarca_client.main._schedule')
    def test_args_schedule_hourly(self, mock_schedule):
        main.main(['schedule', '--hourly'])
        if IS_WINDOWS:
            mock_schedule.assert_called_once_with(schedule=Settings.HOURLY, username=None, password=None)
        else:
            mock_schedule.assert_called_once_with(schedule=Settings.HOURLY)

    @mock.patch('minarca_client.main._schedule')
    def test_args_schedule_weekly(self, mock_schedule):
        main.main(['schedule', '--weekly'])
        if IS_WINDOWS:
            mock_schedule.assert_called_once_with(schedule=Settings.WEEKLY, username=None, password=None)
        else:
            mock_schedule.assert_called_once_with(schedule=Settings.WEEKLY)

    @mock.patch('minarca_client.main._status')
    def test_args_status(self, mock_status):
        main.main(['status'])
        mock_status.assert_called_once_with()

    @mock.patch('minarca_client.main._unlink')
    def test_args_unlink(self, mock_unlink):
        main.main(['unlink'])
        mock_unlink.assert_called_once_with()

    @mock.patch('minarca_client.main.Backup')
    def test_backup(self, mock_backup):
        _backup(force=False)
        mock_backup.return_value.backup.assert_called_once_with(force=False)

    @mock.patch('minarca_client.main.Backup')
    def test_backup_force(self, mock_backup):
        _backup(force=True)
        mock_backup.return_value.backup.assert_called_once_with(force=True)

    @mock.patch('rdiffbackup.run.main_run', return_value=0)
    def test_rdiff_backup(self, mock_main_run):
        # Given multiple arguments pass to rdiff-backup subcommand
        args = ['rdiff-backup', '-v', 'test']
        # When calling rdiff-backup subcommand
        main.main(args)
        # Then all arguments are passed to rdiff-backup function.
        mock_main_run.assert_called_once_with(args[1:])

    def test_rdiff_backup_invalid_args(self):
        # Given multiple arguments pass to rdiff-backup subcommand
        args = ['rdiff-backup', '--some-invalid-args']
        # When calling rdiff-backup subcommand
        # Then a SystemExit is raised
        with self.assertRaises(SystemExit) as capture:
            main.main(args)
        # Then error code is 2
        self.assertEqual(2, capture.exception.code)

    @mock.patch('minarca_client.main.Backup')
    def test_exclude(self, mock_backup):
        p = Patterns('pattern.txt')
        mock_backup.return_value.get_patterns.return_value = p
        main.main(['exclude', '*.bak'])
        mock_backup.return_value.set_patterns.assert_called_once_with(p)
        self.assertEqual([Pattern(False, '*.bak', None)], p)

    @mock.patch('minarca_client.main.Backup')
    def test_include(self, mock_backup):
        p = Patterns('pattern.txt')
        mock_backup.return_value.get_patterns.return_value = p
        main.main(['include', '*.bak'])
        mock_backup.return_value.set_patterns.assert_called_once_with(p)
        self.assertEqual([Pattern(True, '*.bak', None)], p)

    def test_include_duplicate(self):
        # When calling include multiple time with the same value
        # Not using real path for the test since those get resolve differently on Linux and windows.
        main.main(['include', '*.bak'])
        main.main(['include', '*.bak'])
        # Then we don't have duplicate pattern in config file.
        backup = Backup()
        self.assertEqual(
            backup.get_patterns(),
            [Pattern(include=True, pattern='*.bak', comment=None)],
        )

    def test_include_exclude(self):
        # When galling include multiple time with the same value
        # Not using real path for the test since those get resolve differently on Linux and windows.
        main.main(['include', '*.bak'])
        # Then an error is raised
        main.main(['exclude', '*.bak'])
        # Then we kept the include pattern.
        backup = Backup()
        self.assertEqual(
            backup.get_patterns(),
            [Pattern(include=False, pattern='*.bak', comment=None)],
        )

    @mock.patch('minarca_client.main.Backup')
    def test_include_relative_path(self, mock_backup):
        p = Patterns('pattern.txt')
        mock_backup.return_value.get_patterns.return_value = p
        _pattern(True, ['.'])
        mock_backup.return_value.set_patterns.assert_called_once_with(p)
        self.assertEqual([Pattern(True, os.getcwd(), None)], p)

    @mock.patch('minarca_client.main.Backup')
    def test_patterns(self, mock_backup):
        # FIXME
        p = Patterns('pattern.txt')
        p.append(Pattern(True, '/home', None))
        p.append(Pattern(False, '*.bak', None))
        mock_backup.return_value.get_patterns.return_value = p
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            main.main(['patterns'])
        self.assertEqual("+/home\n-*.bak\n", f.getvalue())

    @mock.patch('minarca_client.main.Backup')
    def test_start(self, mock_backup):
        _start(force=False)
        mock_backup.return_value.start.assert_called_once_with(force=False)

    @mock.patch('minarca_client.main.Backup')
    def test_stop(self, mock_backup):
        _stop(force=False)
        mock_backup.return_value.stop.assert_called_once_with()

    @mock.patch('minarca_client.main.Backup')
    def test_schedule(self, mock_backup):
        # When calling schedule
        _schedule(schedule=Settings.DAILY)
        # Then schedule is define and job get create
        mock_backup.return_value.set_settings.assert_called_once_with('schedule', Settings.DAILY)

    @mock.patch('minarca_client.main.Backup')
    def test_schedule_hourly(self, mock_backup):
        _schedule(schedule=Settings.HOURLY)
        mock_backup.return_value.set_settings.assert_called_once_with('schedule', Settings.HOURLY)

    @mock.patch('minarca_client.main.Backup')
    def test_status(self, mock_backup):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            _status()
        mock_backup.return_value.get_status.assert_called_once_with()
        self.assertEqual(6, len(f.getvalue().splitlines()))

    def test_status_with_not_configured(self):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            _status()
        self.assertEqual(6, len(f.getvalue().splitlines()))

    @mock.patch('minarca_client.main.Backup')
    def test_unlink(self, mock_backup):
        _unlink()
        mock_backup.return_value.unlink.assert_called_once_with()
