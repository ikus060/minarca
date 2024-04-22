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

from parameterized import parameterized

from minarca_client import main
from minarca_client.core import Backup, BackupInstance, limit
from minarca_client.core.compat import IS_WINDOWS
from minarca_client.core.config import Pattern, Settings
from minarca_client.core.exceptions import HttpAuthenticationError
from minarca_client.main import _EXIT_LINK_ERROR, _backup
from minarca_client.tests.test import MATCH


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
        mock_backup.assert_called_once_with(force=False, limit=limit(None))

    @mock.patch('minarca_client.main._backup')
    def test_args_backup_force(self, mock_backup):
        main.main(['backup', '--force'])
        mock_backup.assert_called_once_with(force=True, limit=limit(None))

    @mock.patch('minarca_client.main._pattern')
    def test_args_exclude(self, mock_pattern):
        main.main(['exclude', '*.bak'])
        mock_pattern.assert_called_once_with(include=False, pattern=['*.bak'], limit=limit(None))

    @mock.patch('minarca_client.main._pattern')
    def test_args_exclude_multiple(self, mock_pattern):
        main.main(['exclude', '*.bak', '$~*', '/proc'])
        mock_pattern.assert_called_once_with(include=False, pattern=['*.bak', '$~*', '/proc'], limit=limit(None))

    @mock.patch('minarca_client.main._pattern')
    def test_args_include(self, mock_pattern):
        main.main(['include', '*.bak'])
        mock_pattern.assert_called_once_with(include=True, pattern=['*.bak'], limit=limit(None))

    @mock.patch('minarca_client.main._pattern')
    def test_args_include_multiple(self, mock_pattern):
        main.main(['include', '*.bak', '$~*', '/proc'])
        mock_pattern.assert_called_once_with(include=True, pattern=['*.bak', '$~*', '/proc'], limit=limit(None))

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

    @mock.patch('minarca_client.ui.app.MinarcaApp')
    def test_args_ui_is_not_linked(self, mock_app):
        # When calling "minarca ui"
        main.main(['ui'])
        # GUI get started with mainloop
        mock_app.return_value.mainloop.assert_called_once()

    @mock.patch('minarca_client.main.Backup', return_value=mock.AsyncMock())
    def test_link(self, mock_backup):
        main.main(
            ['link', '--remoteurl', 'https://localhost', '--username', 'foo', '--password', 'bar', '--name', 'repo']
        )
        mock_backup.return_value.configure_remote.assert_called_once_with(
            remoteurl='https://localhost', username='foo', password='bar', repositoryname='repo', force=False
        )

    @mock.patch('getpass.getpass')
    @mock.patch('minarca_client.main.Backup', return_value=mock.AsyncMock())
    def test_link_prompt_password(self, mock_backup, mock_getpass):
        mock_getpass.return_value = 'bar'
        main.main(['link', '--remoteurl', 'https://localhost', '--username', 'foo', '--name', 'repo'])
        mock_backup.return_value.configure_remote.assert_called_once_with(
            remoteurl='https://localhost', username='foo', password='bar', repositoryname='repo', force=False
        )

    @mock.patch('getpass.getpass')
    @mock.patch('minarca_client.main.Backup', return_value=mock.AsyncMock())
    def test_link_prompt_password_null(self, mock_backup, mock_getpass):
        mock_getpass.return_value = ''
        with self.assertRaises(SystemExit):
            main.main(['link', '--remoteurl', 'https://localhost', '--username', 'foo', '--name', 'repo'])

    @mock.patch('getpass.getpass')
    @mock.patch('minarca_client.main.Backup')
    def test_link_wrong_password(self, mock_backup, mock_getpass):
        # Given a computer that is not configured
        # Given a wrong password
        mock_getpass.return_value = 'invalid'
        mock_backup.return_value.configure_remote.side_effect = HttpAuthenticationError
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

    @mock.patch('minarca_client.main._patterns')
    def test_args_patterns(self, mock_patterns):
        main.main(['patterns'])
        mock_patterns.assert_called_once_with(limit=limit(None))

    @parameterized.expand(
        [
            ([], {'delay': 24}),
            (['-d', '2'], {'delay': 2}),
            (['--delay', '3'], {'delay': 3}),
            (['--delay', '-5'], {'delay': -5}),
            (['-c'], {'delay': 0}),
            (['--clear'], {'delay': 0}),
        ]
    )
    @mock.patch('minarca_client.main._pause')
    def test_args_pause(self, args, expected_call, mock_pause):
        main.main(['pause'] + args)
        mock_pause.assert_called_once_with(**expected_call, limit=limit(value=None))

    @parameterized.expand(
        [
            (
                ['/path/to/file'],
                {'restore_time': None, 'force': False, 'paths': ['/path/to/file'], 'destination': None},
            ),
            (
                ['--force', '/path/to/file'],
                {'restore_time': None, 'force': True, 'paths': ['/path/to/file'], 'destination': None},
            ),
            (
                ['--destination', '/dest/path/', '/path/to/file'],
                {'restore_time': None, 'force': False, 'paths': ['/path/to/file'], 'destination': '/dest/path/'},
            ),
            (
                ['--restore-time', '2024-01-13', '/path/to/file'],
                {'restore_time': '2024-01-13', 'force': False, 'paths': ['/path/to/file'], 'destination': None},
            ),
        ]
    )
    @mock.patch('minarca_client.main._restore')
    def test_args_restore(self, args, expected_call, mock_restore):
        main.main(['restore'] + args)
        mock_restore.assert_called_once_with(**expected_call, limit=limit(None))

    @mock.patch('minarca_client.main._stop')
    def test_args_stop(self, mock_stop):
        main.main(['stop'])
        mock_stop.assert_called_once_with(force=False, limit=limit(None))

    @mock.patch('minarca_client.main._stop')
    def test_args_stop_force(self, mock_stop):
        main.main(['stop', '--force'])
        mock_stop.assert_called_once_with(force=True, limit=limit(None))

    @mock.patch('minarca_client.main._schedule')
    def test_args_schedule(self, mock_schedule):
        main.main(['schedule'])
        if IS_WINDOWS:
            mock_schedule.assert_called_once_with(
                schedule=Settings.DAILY, username=None, password=None, limit=limit(value=None)
            )
        else:
            mock_schedule.assert_called_once_with(schedule=Settings.DAILY, limit=limit(value=None))

    @mock.patch('minarca_client.main._status')
    def test_args_status(self, mock_status):
        main.main(['status'])
        mock_status.assert_called_once_with(limit=limit(None))

    @mock.patch('minarca_client.main._forget')
    def test_args_forget(self, mock_forget):
        main.main(['forget'])
        mock_forget.assert_called_once_with(limit=limit(None), force=False)

    @mock.patch('minarca_client.main.Backup')
    def test_backup(self, mock_backup):
        # Given a backup instance
        instance = mock.AsyncMock()
        mock_backup.return_value.__getitem__.return_value = [instance]
        # Calling backup with arguments.
        _backup(force=False, limit=limit(None))
        # Then backup get triggered with force=false
        instance.backup.assert_called_once_with(force=False)

    @mock.patch('minarca_client.main.Backup')
    def test_backup_force(self, mock_backup):
        # Given a backup instance
        instance = mock.AsyncMock()
        mock_backup.return_value.__getitem__.return_value = [instance]
        # Calling backup with --force
        _backup(force=True, limit=limit(None))
        # Then backup get triggered with force=false
        instance.backup.assert_called_once_with(force=True)

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

    def test_exclude(self):
        # Given a backup instance
        instance = BackupInstance('')
        instance.settings.configured = True
        instance.settings.save()
        # Calling exclude
        main.main(['exclude', '*.bak'])
        # Then pattern get updated.
        instance.patterns.reload()
        self.assertEqual([Pattern(False, '*.bak', None)], list(instance.patterns))

    def test_include(self):
        # Given a backup instance
        instance = BackupInstance('')
        instance.settings.configured = True
        instance.settings.save()
        # When calling include
        main.main(['include', '*.bak'])
        # Then patterns get updated.
        instance.patterns.reload()
        self.assertEqual([Pattern(True, '*.bak', None)], list(instance.patterns))

    def test_include_duplicate(self):
        # Given a backup instance
        instance = BackupInstance('')
        instance.settings.configured = True
        instance.settings.save()
        # When calling include multiple time with the same value
        # Not using real path for the test since those get resolve differently on Linux and windows.
        main.main(['include', '*.bak'])
        main.main(['include', '*.bak'])
        # Then we don't have duplicate pattern in config file.
        instance.patterns.reload()
        self.assertEqual(
            list(instance.patterns),
            [Pattern(include=True, pattern='*.bak', comment=None)],
        )

    def test_include_exclude(self):
        # Given a backup instance
        instance = BackupInstance('')
        instance.settings.configured = True
        instance.settings.save()
        # When galling include multiple time with the same value
        # Not using real path for the test since those get resolve differently on Linux and windows.
        main.main(['include', '*.bak'])
        # Then an error is raised
        main.main(['exclude', '*.bak'])
        # Then we kept the include pattern.
        instance.patterns.reload()
        self.assertEqual(
            list(instance.patterns),
            [Pattern(include=False, pattern='*.bak', comment=None)],
        )

    def test_include_relative_path(self):
        # Given a backup instance
        instance = BackupInstance('')
        instance.settings.configured = True
        instance.settings.save()
        # When add include pattern with relative path.
        main.main(['include', '.'])
        # Then pattern get updated
        instance.patterns.reload()
        self.assertEqual([Pattern(True, os.getcwd(), None)], list(instance.patterns))

    def test_patterns(self):
        # Given a backup instance
        instance = BackupInstance('')
        instance.settings.configured = True
        instance.settings.save()
        p = instance.patterns
        p.append(Pattern(True, '/home', None))
        p.append(Pattern(False, '*.bak', None))
        p.save()
        # When shoing patterns list.
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            main.main(['patterns'])

        # Then is return the list of pattern on stdout.
        self.assertEqual("+/home\n-*.bak\n", f.getvalue())

    def test_pause(self):
        # Given a backup instance
        instance = BackupInstance('')
        instance.settings.configured = True
        instance.settings.save()
        self.assertIsNone(instance.settings.pause_until)
        # When pausing backups
        main.main(['pause', '--delay', '123'])
        # Then Backup is paused
        instance.settings.reload()
        self.assertIsNotNone(instance.settings.pause_until)

    @mock.patch('minarca_client.main.Backup')
    def test_restore(self, mock_backup):
        # Given a backup instance
        instance = mock.AsyncMock()
        mock_backup.return_value.__getitem__.return_value = [instance]
        # When calling restore
        main.main(['restore', '--force', './test'])
        # Then the first instance is used for restore.
        instance.restore.assert_called_once_with(restore_time=None, paths=[MATCH('*/test')], destination=None)

    @mock.patch('minarca_client.main.Backup')
    def test_restore_with_destination(self, mock_backup):
        # Given a backup instance
        instance = mock.AsyncMock()
        mock_backup.return_value.__getitem__.return_value = [instance]
        # When calling restore
        main.main(['restore', '--force', '--destination', '/tmp', './test'])
        # Then the first instance is used for restore.
        instance.restore.assert_called_once_with(restore_time=None, paths=[MATCH('*/test')], destination='/tmp')

    @mock.patch('minarca_client.main.Backup')
    def test_start(self, mock_backup):
        # Given a backup instance
        instance = mock.MagicMock()
        mock_backup.return_value.__getitem__.return_value = [instance]
        # When calling start
        main.main(['start'])
        # Then start is triggered
        mock_backup.return_value.start_all.assert_called()

    @mock.patch('minarca_client.main.Backup')
    def test_stop(self, mock_backup):
        # Given a backup instance
        instance = mock.MagicMock()
        mock_backup.return_value.__getitem__.return_value = [instance]
        # When calling stop
        main.main(['stop'])
        # Then all instances get stop
        instance.stop.assert_called_once_with()

    def test_schedule(self):
        # Given a backup instance
        instance = BackupInstance('')
        instance.settings.configured = True
        instance.settings.save()
        # When calling schedule
        main.main(['schedule', '--daily'])
        # Then schedule is define and job get create
        self.assertEqual(instance.settings.schedule, Settings.DAILY)

    @parameterized.expand(
        [
            ('--hourly', Settings.HOURLY),
            ('--daily', Settings.DAILY),
            ('--weekly', Settings.WEEKLY),
        ]
    )
    def test_schedule_hourly(self, arg, value):
        # Given a backup instance
        instance = BackupInstance('')
        instance.settings.configured = True
        instance.settings.save()
        # When calling schedule
        main.main(['schedule', arg])
        # Then schedule is define and job get create
        instance.settings.reload()
        self.assertEqual(instance.settings.schedule, value)

    def test_status(self):
        # Given a backup instance
        instance = BackupInstance('')
        instance.settings.configured = True
        instance.settings.save()
        # When calling status
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            main.main(['status'])
        # Then status get printed to stdout
        self.assertIn('Backup Instance:', f.getvalue())
        self.assertIn('Connectivity status:', f.getvalue())
        self.assertIn('Last successful backup:', f.getvalue())
        self.assertIn('Last backup date:', f.getvalue())
        self.assertIn('Last backup status:', f.getvalue())

    def test_forget(self):
        # Given a backup instance
        instance = BackupInstance('')
        instance.settings.configured = True
        instance.settings.save()
        backup = Backup()
        self.assertEqual(1, len(backup))
        # When calling forget
        main.main(['forget', '--force'])
        # Then backup instance get removed
        self.assertEqual(0, len(backup))

    def test_invalid_limit(self):
        # Given a backup instances
        instance = BackupInstance('')
        instance.settings.configured = True
        instance.settings.save()
        backup = Backup()
        self.assertEqual(1, len(backup))
        # When trying to list status with invalid limit
        # Then application raise an exception.
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            with self.assertRaises(SystemExit) as cm:
                main.main(['status', '--limit', 'invalid'])
        self.assertEqual(cm.exception.code, 1)
