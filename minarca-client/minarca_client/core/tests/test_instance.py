# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import os
import subprocess
import tempfile
import unittest
from datetime import timedelta
from unittest import mock
from unittest.case import skipIf, skipUnless
from unittest.mock import MagicMock

import responses

from minarca_client.core import Backup, BackupInstance
from minarca_client.core.compat import IS_WINDOWS
from minarca_client.core.config import Datetime, Pattern, Patterns, Settings
from minarca_client.core.exceptions import (
    BackupError,
    HttpAuthenticationError,
    HttpConnectionError,
    HttpInvalidUrlError,
    HttpServerError,
    NoPatternsError,
    NotConfiguredError,
    NotScheduleError,
    RepositoryNameExistsError,
    UnknownHostException,
    InvalidRepositoryName,
)
from minarca_client.locale import gettext as _
from minarca_client.tests.test import MATCH

IDENTITY = """[test.minarca.net]:2222 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK/Qng4S5d75rtYxklVdIkPiz4paf2pdnCEshUoailQO root@sestican
[test.minarca.net]:2222 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBCi0uz4rVsLpVl8b6ozYzL+t1Lh9P98a0tY7KqAtzFupjtZivdIYxh6jXPeonYo7egY+mFgMX22Tlrth8woRa2M= root@sestican
[test.minarca.net]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+XU4xipQJUKqGshBeCBH7vNfeDgIOXQeaz6Q4S9QbWM39gTUedCfQuabUjXUJafPX8RfEe2xKALaHOdHzT1HYq3GL8oUa4C1J3xkabnZbxA06Ko4Ya31S84G/S+L8kwZ7PmxegZedk6Za49uxBjl/2lBQM4B/BgNccQ9Ifu5Kw4gmU6mfIOZxJ9qx0rF87cXXi5b6o7GMNbK6UViheZvyJQNuR8oYdMEqaVyezJGfSOEFWPm+mQm19Tu4Ad9ElyMyA8SImQshOz7YupEeb26sLvvVwl0EyirMwlI8NIt66DGEy5s2egorL3COB+L0Yp2wjLvzHBMr0Dwb/ZLJfbGR root@sestican
"""

_original_subprocess_popen = subprocess.Popen

# A couple of variable to make stuff cross-platform
_echo_foo_cmd = ['cmd.exe', '/c', 'echo foo'] if IS_WINDOWS else ['echo', 'foo']
_exit_1_cmd = ['cmd.exe', '/c', 'exit 1'] if IS_WINDOWS else ['exit 1']
_ssh = 'ssh.exe' if IS_WINDOWS else '/usr/bin/ssh'
_home = 'C:/Users' if IS_WINDOWS else '/home'
_root = 'C:/' if IS_WINDOWS else '/'


def mock_subprocess_link(*args, **kwargs):
    """
    Mock function to avoid calling the real rdiff-backup command. But during linking, we also make call to ssh keygen.
    """

    if 'rdiff-backup' in args[0][1]:
        return _original_subprocess_popen(_echo_foo_cmd, **kwargs)
    return _original_subprocess_popen(*args, **kwargs)


def mock_subprocess_popen(replace_cmd):
    def mock_call(*args, **kwargs):
        return _original_subprocess_popen(replace_cmd, **kwargs)

    return mock_call


class TestBackupInstance(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        os.environ['MINARCA_CONFIG_HOME'] = self.tmp.name
        os.environ['MINARCA_DATA_HOME'] = self.tmp.name
        self.backup = Backup()
        self.backup.scheduler = MagicMock()
        self.instance = BackupInstance('1')

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()
        del os.environ['MINARCA_CONFIG_HOME']
        del os.environ['MINARCA_DATA_HOME']

    def test_link_with_empty_repository_name(self):
        with self.assertRaises(InvalidRepositoryName):
            self.backup.configure_remote("http://localhost", "admin", "admin", "")

    def test_link_with_invalid_repository_name(self):
        with self.assertRaises(InvalidRepositoryName):
            self.backup.configure_remote("http://localhost", "admin", "admin", "invalid!?%$/")

    @responses.activate
    def test_link_with_existing_repository_name(self):
        # Mock some https stuff
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            json={'email': 'admin@example.com', 'username': 'admin', 'repos': [{'name': 'coucou'}]},
        )
        responses.add(
            responses.GET,
            "http://localhost/api/minarca/",
            json={'remotehost': 'remote', 'version': '3.9.0', 'identity': IDENTITY},
        )
        responses.add(responses.POST, "http://localhost/api/currentuser/sshkeys", status=200)

        # Check with identical repo name
        with self.assertRaises(RepositoryNameExistsError):
            self.backup.configure_remote("http://localhost", "admin", "admin", "coucou")

        # Check with sub folders
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            json={'email': 'admin@example.com', 'username': 'admin', 'repos': [{'name': 'coucou/C'}]},
        )
        with self.assertRaises(RepositoryNameExistsError):
            self.backup.configure_remote("http://localhost", "admin", "admin", "coucou")

    @responses.activate
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_existing_patterns(self, mock_popen):
        # Create patterns
        self.instance.patterns.append(Pattern(True, _home, None))
        initial_patterns = list(self.instance.patterns)

        # Mock some https stuff
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            json={'email': 'admin@example.com', 'username': 'admin', 'repos': []},
        )
        responses.add(
            responses.GET,
            "http://localhost/api/minarca/",
            json={'remotehost': 'remote', 'version': '3.9.0', 'identity': IDENTITY},
        )
        responses.add(responses.POST, "http://localhost/api/currentuser/sshkeys", status=200)

        # When linking the instance
        self.instance = self.backup.configure_remote("http://localhost", "admin", "admin", "coucou", instance=self.instance)

        # Check calls to web api
        responses.assert_call_count("http://localhost/api/", 1)
        responses.assert_call_count("http://localhost/api/currentuser/", 1)
        responses.assert_call_count("http://localhost/api/minarca/", 1)
        responses.assert_call_count("http://localhost/api/currentuser/sshkeys", 1)

        # Check if rdiff_backup get called.
        self.assertEqual(2, mock_popen.call_count)

        # Then initial pattern are kept.
        patterns = self.instance.patterns
        self.assertEqual(initial_patterns, list(patterns))

    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_http_invalid_url_error(self, *unused):
        # Link
        with self.assertRaises(HttpInvalidUrlError):
            self.backup.configure_remote("not_http_url", "admin", "admin", "coucou")

    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_http_invalid_url_error_2(self, *unused):
        # Link
        with self.assertRaises(HttpInvalidUrlError):
            self.backup.configure_remote("ssh://localhost", "admin", "admin", "coucou")

    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_http_connection_error(self, *unused):
        # Link
        with self.assertRaises(HttpConnectionError):
            self.backup.configure_remote("http://invalid_host_name", "admin", "admin", "coucou")

    @responses.activate
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_http_authentication_error_401(self, *unused):
        # Mock authentication fail
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(responses.GET, "http://localhost/api/currentuser/", status=401)

        # Link
        with self.assertRaises(HttpAuthenticationError):
            self.backup.configure_remote("http://localhost", "admin", "admin", "coucou")

    @responses.activate
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_http_authentication_error_403(self, *unused):
        # Mock authentication fail
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(responses.GET, "http://localhost/api/currentuser/", status=403)

        # Link
        with self.assertRaises(HttpAuthenticationError):
            self.backup.configure_remote("http://localhost", "admin", "admin", "coucou")

    @responses.activate
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_http_authentication_error_503(self, *unused):
        # Mock authentication fail
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(responses.GET, "http://localhost/api/currentuser/", status=503)

        # Link
        with self.assertRaises(HttpServerError):
            self.backup.configure_remote("http://localhost", "admin", "admin", "coucou")

    @responses.activate
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link(self, mock_popen):
        # Define a status
        status = self.instance.status
        status.lastresult = 'SUCCESS'
        status.save()
        status.reload()
        self.assertEqual('SUCCESS', status.lastresult)

        # Mock some https stuff
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            json={'email': 'admin@example.com', 'username': 'admin', 'repos': []},
        )
        responses.add(
            responses.GET,
            "http://localhost/api/minarca/",
            json={'remotehost': 'remote', 'version': '3.9.0', 'identity': IDENTITY},
        )
        responses.add(responses.POST, "http://localhost/api/currentuser/sshkeys", status=200)

        # Link
        self.instance = self.backup.configure_remote("http://localhost", "admin", "admin", "coucou")

        # Check calls to web api
        responses.assert_call_count("http://localhost/api/", 1)
        responses.assert_call_count("http://localhost/api/currentuser/", 1)
        responses.assert_call_count("http://localhost/api/minarca/", 1)
        responses.assert_call_count("http://localhost/api/currentuser/sshkeys", 1)
        mock_popen.assert_called()

        # Check if default patterns are created
        patterns = self.instance.patterns
        self.assertTrue(len(patterns) > 0)

        # Check if default status is set.
        self.assertEqual('UNKNOWN', self.instance.status.lastresult)

    @skipIf(IS_WINDOWS, 'linux/macos specific test')
    def test_get_repo_url_linux(self):
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.remoteurl = 'http://remotehost'
        config.repositoryname = 'test-repo'
        config.username = 'username'
        config.save()
        # Get value
        self.assertEqual('http://remotehost/browse/username/test-repo', self.instance.get_repo_url())

    @skipUnless(IS_WINDOWS, 'windows specific test')
    def test_get_repo_url_windows(self):
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.remoteurl = 'http://remotehost'
        config.repositoryname = 'test-repo'
        config.username = 'username'
        config.save()
        self.instance.patterns.extend(Patterns.defaults())
        self.instance.patterns.save()
        # Get value
        self.assertEqual('http://remotehost/browse/username/test-repo/C', self.instance.get_repo_url())

    def test_get_help_url(self):
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.remoteurl = 'http://remotehost'
        config.repositoryname = 'test-repo'
        config.username = 'username'
        config.save()
        # Get value
        self.assertEqual('http://remotehost/help', self.instance.get_help_url())

    def test_get_status(self):
        self.assertIsNotNone(self.instance.status)

    def test_get_status_with_interupt(self):
        # Mock the status file.
        status = self.instance.status
        status.lastresult = 'RUNNING'
        status.lastdate = Datetime()
        # Check status
        status = self.instance.status
        self.assertEqual('INTERRUPT', status.current_status)

    def test_get_status_with_running(self):
        # Mock the status file.
        status = self.instance.status
        status.lastresult = 'RUNNING'
        status.lastdate = Datetime()
        status.pid = os.getpid()
        # Check status
        self.assertEqual('RUNNING', status.current_status)

    def test_get_status_with_stale(self):
        # Mock the status file.
        status = self.instance.status
        status.lastresult = 'RUNNING'
        status.lastdate = Datetime(1625486954000)
        status.pid = os.getpid()
        # Check status
        self.assertEqual('STALE', status.current_status)

    def test_is_backup_time_lastsuccess_none(self):
        status = self.instance.status
        status.lastsuccess = None
        self.assertTrue(self.instance.is_backup_time())

    def test_is_backup_time_lastsuccess_past(self):
        status = self.instance.status
        status.lastsuccess = Datetime(1592847257000)
        self.assertTrue(self.instance.is_backup_time())

    def test_is_backup_time_lastsuccess_now(self):
        status = self.instance.status
        status.lastsuccess = Datetime()
        self.assertFalse(self.instance.is_backup_time())

    def test_is_backup_time_pause_until(self):
        # Given a backup that did not ran for a while
        status = self.instance.status
        status.lastsuccess = Datetime(1592847257000)
        self.assertTrue(self.instance.is_backup_time())
        # When pausing the backup
        self.instance.settings.pause_until = Datetime() + timedelta(minutes=1)
        # Then backup is paused
        self.assertFalse(self.instance.is_backup_time())
        # When pause is finish
        self.instance.settings.pause_until = Datetime()
        # Then backup could start
        self.assertTrue(self.instance.is_backup_time())

    def test_is_running_no_pid(self):
        status = self.instance.status
        status.lastresult = 'SUCCESS'
        self.assertFalse(self.instance.is_running())

    def test_is_running_not_running_pid(self):
        status = self.instance.status
        status.lastresult = 'RUNNING'
        status.pid = 9812345678
        self.assertFalse(self.instance.is_running())

    def test_is_running_running_pid(self):
        status = self.instance.status
        status.lastresult = 'RUNNING'
        status.pid = os.getpid()
        self.assertTrue(self.instance.is_running())

    def test_pause(self):
        # When backup never ran
        self.assertTrue(self.instance.is_backup_time())
        # When pausing backup for 24 hours
        self.instance.pause(24)
        # Then pause delay is computed
        pause_until = self.instance.settings.pause_until
        self.assertAlmostEqual(pause_until, Datetime() + timedelta(hours=24), delta=timedelta(minutes=1))
        # Then it's not time to backup
        self.assertFalse(self.instance.is_backup_time())

    def test_pause_zero(self):
        # Given backup is paused
        self.instance.pause(24)
        self.assertFalse(self.instance.is_backup_time())
        # When removing pause
        self.instance.pause(0)
        # Then backup could resume
        self.assertIsNone(self.instance.settings.pause_until)
        self.assertTrue(self.instance.is_backup_time())

    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_popen(_echo_foo_cmd))
    def test_pause_with_backup_force(self, unused):
        # Provide default config
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.configured = True
        config.save()
        patterns = self.instance.patterns
        patterns.append(Pattern(True, _home, None))
        patterns.save()
        self.instance._rdiff_backup = MagicMock()
        # Given a backup pause for 24 hours
        self.instance.pause(24)
        with self.assertRaises(NotScheduleError):
            self.instance.backup()
        # When running backup with --force
        self.instance.backup(force=True)
        # Then backup is unpaused
        self.assertIsNone(self.instance.settings.pause_until)

    @mock.patch('minarca_client.core.compat.get_ssh', return_value=_ssh)
    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_popen(_echo_foo_cmd))
    def test_rdiff_backup(self, mock_rdiff_backup, *unused):
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.save()
        # When calling rdiff_backup with any argument
        self.instance._rdiff_backup('backup', 'any-argument')
        # Then is trigger a call to rdiff_backup function with the same arguments
        mock_rdiff_backup.assert_called_once_with(
            [mock.ANY, 'rdiff-backup', '-v', '5', 'backup', 'any-argument'],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding='utf-8',
            errors='replace',
        )

    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_popen(_exit_1_cmd))
    def test_rdiff_backup_return_error(self, mock_popen, *unused):
        # Given a configured backup instance
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.save()
        # When executing rdiff-backup return exit-code 1 (see mock)
        # Then an exception is raised.
        with self.assertRaises(BackupError):
            self.instance._rdiff_backup('backup', 'any-arguments')

    def test_rdiff_backup_unknown_host(self):
        # Given rdiff-backup started in a separate thread
        # With invalid remote host.
        config = self.instance.settings
        config.remotehost = 'invalid-remotehost:2222'
        config.repositoryname = 'test-repo'
        config.save()
        self.instance.patterns.extend(Patterns.defaults())
        self.instance.patterns.save()
        # When rdiff-backup isrunning
        # Then it should exit with error code 1
        with self.assertRaises(UnknownHostException):
            self.instance.backup()

    def test_backup_not_configured_remotehost(self):
        config = self.instance.settings
        config.remotehost = ''
        config.repositoryname = 'test-repo'
        config.save()
        self.instance.patterns.extend(Patterns.defaults())
        self.instance.patterns.save()
        # Make the call
        with self.assertRaises(NotConfiguredError):
            self.instance.backup()

    def test_backup_not_configured_repositoryname(self):
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = ''
        config.save()
        self.instance.patterns.extend(Patterns.defaults())
        self.instance.patterns.save()
        # Make the call
        with self.assertRaises(NotConfiguredError):
            self.instance.backup()

    def test_set_schedule(self):
        self.instance.settings.schedule = Settings.HOURLY
        self.assertEqual(Settings.HOURLY, self.instance.settings.schedule)

    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_popen(_echo_foo_cmd))
    def test_backup(self, mock_popen, *unused):
        start_time = Datetime()
        # Mock call to rdiff-backup
        self.instance._rdiff_backup = MagicMock()
        # Provide default config
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.configured = True
        config.save()
        patterns = self.instance.patterns
        patterns.append(Pattern(True, _home, None))
        patterns.save()
        self.instance.backup()
        # Check if rdiff-backup is called.
        if IS_WINDOWS:
            self.instance._rdiff_backup.assert_called_once_with(
                '--remote-schema',
                mock.ANY,
                'backup',
                '--no-hard-links',
                '--exclude-symbolic-links',
                '--create-full-path',
                '--no-compression',
                '--include',
                _home,
                '--exclude',
                'C:/**',
                'C:/',
                'minarca@remotehost::test-repo/C/',
                log_file=mock.ANY,
            )
        else:
            self.instance._rdiff_backup.assert_called_once_with(
                '--remote-schema',
                mock.ANY,
                'backup',
                '--exclude-sockets',
                '--no-compression',
                '--include',
                _home,
                '--exclude',
                '/**',
                '/',
                'minarca@remotehost::test-repo/',
                log_file=mock.ANY,
            )
        # Check status
        status = self.instance.status
        status.reload()
        self.assertEqual('SUCCESS', status.lastresult)
        self.assertTrue(status.lastsuccess > start_time)
        self.assertEqual(status.lastdate, status.lastsuccess)
        self.assertEqual('', status.details)

    def test_backup_not_scheduled(self):
        status = self.instance.status
        status.lastsuccess = Datetime()
        with self.assertRaises(NotScheduleError):
            self.instance.backup()

    def test_start_without_patterns(self):
        start_time = Datetime()
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.configured = True
        config.save()
        with self.assertRaises(NoPatternsError):
            self.instance.backup()
        # Check status
        status = self.instance.status
        status.reload()
        self.assertTrue(status.lastdate > start_time)
        self.assertNotEqual(status.lastdate, status.lastsuccess)
        self.assertEqual('FAILURE', status.lastresult)
        self.assertEqual(_('include patterns are missing'), status.details)

    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('minarca_client.core.compat.get_ssh', return_value=_ssh)
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_popen(_echo_foo_cmd))
    def test_test_connection(self, mock_rdiff_backup, *unused):
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.save()
        self.instance.test_connection()
        # Validate
        mock_rdiff_backup.assert_called_once_with(
            [
                mock.ANY,
                'rdiff-backup',
                '-v',
                '5',
                '--remote-schema',
                MATCH(
                    _ssh
                    + " -oBatchMode=yes -oPreferredAuthentications=publickey -oUserKnownHostsFile=*known_hosts? -oIdentitiesOnly=yes -i *id_rsa? %s 'minarca/* rdiff-backup/2.0.0 (*)'"
                ),
                'test',
                'minarca@remotehost::.',
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding='utf-8',
            errors='replace',
        )

    def test_forget(self):
        # Mock a configuration
        config = Settings(self.instance.config_file)
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.configured = True
        config.save()
        # forget
        self.instance.forget()
        config = self.instance.settings
        self.assertEqual(False, config.configured)

    @mock.patch('minarca_client.core.compat.get_ssh', return_value=_ssh)
    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    def test_remote_schema(self, *unused):
        # Given a backup instance configured with a remote port
        config = self.instance.settings
        config.remotehost = 'remotehost:2222'
        config.repositoryname = 'test-repo'
        config.save()
        # Then when generating the remote schema
        value = self.instance._remote_schema()
        # Then the port is defined in the value
        self.assertEqual(
            value,
            MATCH(
                _ssh
                + " -oBatchMode=yes -oPreferredAuthentications=publickey -p 2222 -oUserKnownHostsFile=*known_hosts? -oIdentitiesOnly=yes -i *id_rsa? %s 'minarca/DEV rdiff-backup/2.0.0 (os info)'"
            ),
        )
