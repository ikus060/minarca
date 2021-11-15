# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from minarca_client.core import (Backup, BackupError, HttpAuthenticationError,
                                 HttpConnectionError, HttpInvalidUrlError, NoPatternsError, NotScheduleError,
                                 RepositoryNameExistsError)
from minarca_client.core.compat import IS_WINDOWS
from minarca_client.core.config import Datetime, Pattern, Patterns, Settings
from minarca_client.tests.test import MATCH
from unittest import mock
from unittest.case import skipIf, skipUnless
from unittest.mock import MagicMock
import os
import responses
import subprocess
import tempfile
import threading
import unittest
from minarca_client.core.exceptions import NotConfiguredError, HttpServerError, SshConnectionError

IDENTITY = """[test.minarca.net]:2222 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK/Qng4S5d75rtYxklVdIkPiz4paf2pdnCEshUoailQO root@sestican
[test.minarca.net]:2222 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBCi0uz4rVsLpVl8b6ozYzL+t1Lh9P98a0tY7KqAtzFupjtZivdIYxh6jXPeonYo7egY+mFgMX22Tlrth8woRa2M= root@sestican
[test.minarca.net]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+XU4xipQJUKqGshBeCBH7vNfeDgIOXQeaz6Q4S9QbWM39gTUedCfQuabUjXUJafPX8RfEe2xKALaHOdHzT1HYq3GL8oUa4C1J3xkabnZbxA06Ko4Ya31S84G/S+L8kwZ7PmxegZedk6Za49uxBjl/2lBQM4B/BgNccQ9Ifu5Kw4gmU6mfIOZxJ9qx0rF87cXXi5b6o7GMNbK6UViheZvyJQNuR8oYdMEqaVyezJGfSOEFWPm+mQm19Tu4Ad9ElyMyA8SImQshOz7YupEeb26sLvvVwl0EyirMwlI8NIt66DGEy5s2egorL3COB+L0Yp2wjLvzHBMr0Dwb/ZLJfbGR root@sestican
"""

_original_subprocess_popen = subprocess.Popen

# A couple of variable to make stuff cross-platform
_echo_foo_cmd = ['cmd.exe', '/c',
                 'echo foo'] if IS_WINDOWS else ['echo', 'foo']
_exit_1_cmd = ['cmd.exe', '/c',
               'exit 1'] if IS_WINDOWS else ['sh', '-c', 'exit 1']
_ssh = 'ssh.exe' if IS_WINDOWS else '/usr/bin/ssh'
_home = 'C:/Users' if IS_WINDOWS else '/home'
_root = 'C:/' if IS_WINDOWS else '/'


def mock_subprocess_link(*args, **kwargs):
    if 'rdiff-backup' in args[0][0]:
        return _original_subprocess_popen(_echo_foo_cmd, **kwargs)
    return _original_subprocess_popen(*args, **kwargs)


def mock_subprocess_popen(replace_cmd):

    def mock_call(*args, **kwargs):
        return _original_subprocess_popen(replace_cmd, **kwargs)

    return mock_call


class TestBackup(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        os.environ['MINARCA_CONFIG_HOME'] = self.tmp.name
        os.environ['MINARCA_DATA_HOME'] = self.tmp.name
        self.backup = Backup()

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()
        del os.environ['MINARCA_CONFIG_HOME']
        del os.environ['MINARCA_DATA_HOME']

    def test_link_with_empty_repository_name(self):
        with self.assertRaises(ValueError):
            self.backup.link("http://localhost", "admin", "admin", "")

    def test_link_with_invalid_repository_name(self):
        with self.assertRaises(ValueError):
            self.backup.link("http://localhost", "admin",
                             "admin", "invalid!?%$/")

    @mock.patch("minarca_client.core.Rdiffweb")
    def test_link_with_existing_repository_name(self, mock_rdiffweb):
        # Check with identical repo name
        mock_rdiffweb.return_value.get_current_user_info = mock.MagicMock(
            return_value={'email': 'admin@example.com', 'username': 'admin', 'repos': [{'name': 'coucou'}]})
        with self.assertRaises(RepositoryNameExistsError):
            self.backup.link("http://localhost", "admin", "admin", "coucou")

        # Check with sub folders
        mock_rdiffweb.return_value.get_current_user_info = mock.MagicMock(
            return_value={'email': 'admin@example.com', 'username': 'admin', 'repos': [{'name': 'coucou/C'}]})
        with self.assertRaises(RepositoryNameExistsError):
            self.backup.link("http://localhost", "admin", "admin", "coucou")

    @mock.patch('minarca_client.core.Scheduler')
    @mock.patch('rdiff_backup.Main.Main')
    @mock.patch("minarca_client.core.Rdiffweb")
    def test_link_with_existing_patterns(self, mock_rdiffweb, mock_rdiff_backup, mock_scheduler):
        # Create patterns
        initial_patterns = self.backup.get_patterns()
        initial_patterns.append(Pattern(True, _home, None))
        initial_patterns.save()

        # Mock some https stuff
        mock_rdiffweb.return_value.get_current_user_info = mock.MagicMock(
            return_value={'email': 'admin@example.com', 'username': 'admin', 'repos': []})
        mock_rdiffweb.return_value.get_minarca_info = mock.MagicMock(
            return_value={'remotehost': 'remote', 'version': '3.9.0', 'identity': IDENTITY})

        # Link
        self.backup.link("http://localhost", "admin", "admin", "coucou")

        # Check calls to web api
        mock_rdiffweb.return_value.get_current_user_info.assert_called_once()
        mock_rdiffweb.return_value.add_ssh_key.assert_called_once()
        mock_scheduler.return_value.create.assert_called_once()

        # Check if rdiff_backup get called.
        mock_rdiff_backup.assert_called_once()

        # Check if default patterns are created
        patterns = self.backup.get_patterns()
        self.assertEqual(initial_patterns, patterns)

    @mock.patch('minarca_client.core.Scheduler')
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_http_invalid_url_error(self, *unused):
        # Link
        with self.assertRaises(HttpInvalidUrlError):
            self.backup.link("not_http_url",
                             "admin", "admin", "coucou")

    @mock.patch('minarca_client.core.Scheduler')
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_http_invalid_url_error_2(self, *unused):
        # Link
        with self.assertRaises(HttpInvalidUrlError):
            self.backup.link("ssh://localhost",
                             "admin", "admin", "coucou")

    @mock.patch('minarca_client.core.Scheduler')
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_http_connection_error(self, *unused):
        # Link
        with self.assertRaises(HttpConnectionError):
            self.backup.link("http://invalid_host_name",
                             "admin", "admin", "coucou")

    @responses.activate
    @mock.patch('minarca_client.core.Scheduler')
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_http_authentication_error_401(self, *unused):
        # Mock authentication fail
        responses.add(responses.GET, "http://localhost/")
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            status=401)

        # Link
        with self.assertRaises(HttpAuthenticationError):
            self.backup.link("http://localhost",
                             "admin", "admin", "coucou")

    @responses.activate
    @mock.patch('minarca_client.core.Scheduler')
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_http_authentication_error_403(self, *unused):
        # Mock authentication fail
        responses.add(responses.GET, "http://localhost/")
        responses.add(responses.GET,
                      "http://localhost/api/currentuser/",
                      status=403)

        # Link
        with self.assertRaises(HttpAuthenticationError):
            self.backup.link("http://localhost",
                             "admin", "admin", "coucou")

    @responses.activate
    @mock.patch('minarca_client.core.Scheduler')
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_link)
    def test_link_with_http_authentication_error_503(self, *unused):
        # Mock authentication fail
        responses.add(responses.GET, "http://localhost/")
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            status=503)

        # Link
        with self.assertRaises(HttpServerError):
            self.backup.link("http://localhost",
                             "admin", "admin", "coucou")

    @mock.patch('minarca_client.core.Scheduler')
    @mock.patch('rdiff_backup.Main.Main')
    @mock.patch("minarca_client.core.Rdiffweb")
    def test_link(self, mock_rdiffweb, mock_rdiff_backup, mock_scheduler):
        # Define a status
        with open(self.backup.status_file, 'w') as f:
            f.write('lastresult=SUCCESS\n')
        self.assertEqual('SUCCESS', self.backup.get_status('lastresult'))

        # Mock some https stuff
        mock_rdiffweb.return_value.get_current_user_info = mock.MagicMock(
            return_value={'email': 'admin@example.com', 'username': 'admin', 'repos': []})
        mock_rdiffweb.return_value.get_minarca_info = mock.MagicMock(
            return_value={'remotehost': 'remote', 'version': '3.9.0', 'identity': IDENTITY})

        # Link
        self.backup.link("http://localhost", "admin", "admin", "coucou")

        # Check calls to web api
        mock_rdiffweb.return_value.get_current_user_info.assert_called_once()
        mock_rdiffweb.return_value.add_ssh_key.assert_called_once()
        mock_rdiff_backup.assert_called_once()
        mock_scheduler.return_value.create.assert_called_once()

        # Check if default patterns are created
        patterns = self.backup.get_patterns()
        self.assertTrue(len(patterns) > 0)

        # Check if default status is set.
        self.assertEqual('UNKNOWN', self.backup.get_status('lastresult'))

    @mock.patch('minarca_client.core.Scheduler')
    @mock.patch('rdiff_backup.Main.Main')
    @mock.patch("minarca_client.core.Rdiffweb")
    def test_link_threading(self, mock_rdiffweb, mock_rdiff_backup, mock_scheduler):
        # Mock some https stuff
        mock_rdiffweb.return_value.get_current_user_info = mock.MagicMock(
            return_value={'email': 'admin@example.com', 'username': 'admin', 'repos': []})
        mock_rdiffweb.return_value.get_minarca_info = mock.MagicMock(
            return_value={'remotehost': 'remote', 'version': '3.9.0', 'identity': IDENTITY})

        # Link
        self.error = None

        def _start_link():
            try:
                self.backup.link("http://localhost",
                                 "admin", "admin", "coucou")
            except Exception as e:
                self.error = e

        # Start rdiff-backup in a separate thread.
        thread = threading.Thread(target=_start_link)
        thread.start()
        thread.join()

        # Should not raise any error.
        self.assertIsNone(self.error)

    @skipIf(IS_WINDOWS, 'linux/macos specific test')
    def test_get_remote_url_linux(self):
        config = Settings(self.backup.config_file)
        config['remotehost'] = 'remotehost'
        config['remoteurl'] = 'http://remotehost'
        config['repositoryname'] = 'test-repo'
        config['username'] = 'username'
        config.save()
        # Get value
        self.assertEqual('http://remotehost/browse/username/test-repo',
                         self.backup.get_remote_url())

    @skipUnless(IS_WINDOWS, 'windows specific test')
    def test_get_remote_url_windows(self):
        config = Settings(self.backup.config_file)
        config['remotehost'] = 'remotehost'
        config['remoteurl'] = 'http://remotehost'
        config['repositoryname'] = 'test-repo'
        config['username'] = 'username'
        config.save()
        patterns = self.backup.get_patterns()
        patterns.defaults()
        patterns.save()
        # Get value
        self.assertEqual('http://remotehost/browse/username/test-repo/C',
                         self.backup.get_remote_url())

    def test_get_help_url(self):
        config = Settings(self.backup.config_file)
        config['remotehost'] = 'remotehost'
        config['remoteurl'] = 'http://remotehost'
        config['repositoryname'] = 'test-repo'
        config['username'] = 'username'
        config.save()
        # Get value
        self.assertEqual('http://remotehost/help',
                         self.backup.get_help_url())

    def test_get_status(self):
        status = self.backup.get_status()
        self.assertIsNotNone(status)

    def test_get_status_with_interupt(self):
        # Mock the status file.
        status = self.backup.get_status()
        status['lastresult'] = 'RUNNING'
        status['lastdate'] = Datetime()
        status.save()
        # Check status
        status = self.backup.get_status()
        self.assertEqual('INTERRUPT', status['lastresult'])

    def test_get_status_with_running(self):
        # Mock the status file.
        status = self.backup.get_status()
        status['lastresult'] = 'RUNNING'
        status['lastdate'] = Datetime()
        status['pid'] = os.getpid()
        # Check status
        status.save()
        status = self.backup.get_status()
        self.assertEqual('RUNNING', status['lastresult'])

    def test_get_status_with_stale(self):
        # Mock the status file.
        status = self.backup.get_status()
        status['lastresult'] = 'RUNNING'
        status['lastdate'] = Datetime(1625486954000)
        status['pid'] = os.getpid()
        status.save()
        # Check status
        status = self.backup.get_status()
        self.assertEqual('STALE', status['lastresult'])

    def test_is_backup_time_lastsuccess_none(self):
        status = self.backup.get_status()
        status['lastsuccess'] = None
        status.save()
        self.assertTrue(self.backup.is_backup_time())

    def test_is_backup_time_lastsuccess_past(self):
        status = self.backup.get_status()
        status['lastsuccess'] = Datetime(1592847257000)
        status.save()
        self.assertTrue(self.backup.is_backup_time())

    def test_is_backup_time_lastsuccess_now(self):
        status = self.backup.get_status()
        status['lastsuccess'] = Datetime()
        status.save()
        self.assertFalse(self.backup.is_backup_time())

    def test_is_running_no_pid(self):
        status = self.backup.get_status()
        status['status'] = 'SUCCESS'
        status.save()
        self.assertFalse(self.backup.is_running())

    def test_is_running_not_running_pid(self):
        status = self.backup.get_status()
        status['status'] = 'RUNNING'
        status['pid'] = 9812345678
        status.save()
        self.assertFalse(self.backup.is_running())

    def test_is_running_running_pid(self):
        status = self.backup.get_status()
        status['lastresult'] = 'RUNNING'
        status['pid'] = os.getpid()
        status.save()
        self.assertTrue(self.backup.is_running())

    @mock.patch('minarca_client.core.compat.get_ssh', return_value=_ssh)
    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('rdiff_backup.Main.Main')
    def test_rdiff_backup(self, mock_rdiff_backup, *unused):
        config = Settings(self.backup.config_file)
        config['remotehost'] = 'remotehost'
        config['repositoryname'] = 'test-repo'
        config.save()
        # Make the call
        self.backup._rdiff_backup(
            extra_args=['--include', _home], source=_root)
        # Validate
        mock_rdiff_backup.assert_called_once_with([
            '-v',
            '4',
            '--remote-schema',
            MATCH(_ssh + " -oBatchMode=yes -oPreferredAuthentications=publickey -oUserKnownHostsFile='*known_hosts' -oIdentitiesOnly=yes -i '*id_rsa' %s 'minarca/DEV rdiff-backup/2.0.0 (os info)'"),
            '--include',
            _home,
            _root,
            'minarca@remotehost::test-repo/C' if IS_WINDOWS else 'minarca@remotehost::test-repo'])

    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_popen(_exit_1_cmd))
    def test_rdiff_backup_return_error(self, mock_popen, *unused):
        # Given an invalid remote host
        config = Settings(self.backup.config_file)
        config['remotehost'] = 'remotehost'
        config['repositoryname'] = 'test-repo'
        config.save()
        # When executing rdiff-backup
        # Then an exception is raised.
        with self.assertRaises(BackupError):
            self.backup._rdiff_backup(
                extra_args=['--include', '/home'], source='/',)

    @mock.patch('minarca_client.core.compat.get_ssh', return_value=_ssh)
    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('rdiff_backup.Main.Main')
    def test_rdiff_backup_custom_port(self, mock_rdiff_backup, *unused):
        config = Settings(self.backup.config_file)
        config['remotehost'] = 'remotehost:2222'
        config['repositoryname'] = 'test-repo'
        config.save()
        # Make the call
        self.backup._rdiff_backup(
            extra_args=['--include', _home], source=_root)
        # Validate port numner
        mock_rdiff_backup.assert_called_once_with([
            '-v',
            '4',
            '--remote-schema',
            MATCH(_ssh + " -oBatchMode=yes -oPreferredAuthentications=publickey -p 2222 -oUserKnownHostsFile='*known_hosts' -oIdentitiesOnly=yes -i '*id_rsa' %s 'minarca/DEV rdiff-backup/2.0.0 (os info)'"),
            '--include',
            _home,
            _root,
            'minarca@remotehost::test-repo/C' if IS_WINDOWS else 'minarca@remotehost::test-repo'])

    def test_rdiff_backup_threading(self):

        self.error = None

        def _start_backup():
            try:
                self.backup._rdiff_backup(
                    extra_args=['--include', _home], source=_root)
            except Exception as e:
                self.error = e

        config = Settings(self.backup.config_file)
        config['remotehost'] = 'remotehost:2222'
        config['repositoryname'] = 'test-repo'
        config.save()

        # Start rdiff-backup in a separate thread.
        thread = threading.Thread(target=_start_backup)
        thread.start()
        thread.join()

        # Should exit with error code 1, because remote host cannot beresolved.
        self.assertIsInstance(self.error, SshConnectionError)
        self.assertIsInstance(self.error.__cause__, SystemExit)

    def test_rdiff_backup_not_configured_remotehost(self):
        config = Settings(self.backup.config_file)
        config['remotehost'] = ''
        config['repositoryname'] = 'test-repo'
        config.save()
        # Make the call
        with self.assertRaises(NotConfiguredError):
            self.backup._rdiff_backup(
                extra_args=['--include', '/home'], source='/',)

    def test_rdiff_backup_not_configured_repositoryname(self):
        config = Settings(self.backup.config_file)
        config['remotehost'] = 'remotehost'
        config['repositoryname'] = ''
        config.save()
        # Make the call
        with self.assertRaises(NotConfiguredError):
            self.backup._rdiff_backup(
                extra_args=['--include', '/home'], source='/',)

    @mock.patch('minarca_client.core.compat.get_minarca_exe', return_value='minarca.exe' if IS_WINDOWS else 'minarca')
    def test_schedule(self, *unused):
        self.backup.schedule(schedule=Settings.HOURLY)
        self.assertEqual(Settings.HOURLY, self.backup.get_settings('schedule'))

    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('subprocess.Popen', side_effect=mock_subprocess_popen(_echo_foo_cmd))
    def test_start(self, mock_popen, *unused):
        start_time = Datetime()
        # Mock call to rdiff-backup
        self.backup._rdiff_backup = MagicMock()
        # Provide default config
        config = Settings(self.backup.config_file)
        config['remotehost'] = 'remotehost'
        config['repositoryname'] = 'test-repo'
        config['configured'] = True
        config.save()
        patterns = Patterns(self.backup.patterns_file)
        patterns.append(Pattern(True, _home, None))
        patterns.save()
        self.backup.start()
        # Check if rdiff-backup is called.
        if IS_WINDOWS:
            self.backup._rdiff_backup.assert_called_once_with(
                ['--no-hard-links',
                 '--exclude-symbolic-links',
                 '--create-full-path',
                 '--no-compression',
                 '--include', _home,
                 '--exclude', 'C:/**'],
                source='C:/')
        else:
            self.backup._rdiff_backup.assert_called_once_with(
                ['--exclude-sockets',
                 '--no-compression',
                 '--include', _home,
                 '--exclude', '/**'],
                source='/')
        # Check status
        status = self.backup.get_status()
        self.assertTrue(status['lastsuccess'] > start_time)
        self.assertEqual(status['lastdate'], status['lastsuccess'])
        self.assertEqual('SUCCESS', status['lastresult'])
        self.assertEqual('', status['details'])

    def test_backup_not_scheduled(self):
        status = self.backup.get_status()
        status['lastsuccess'] = Datetime()
        status.save()
        with self.assertRaises(NotScheduleError):
            self.backup.start()

    def test_start_without_patterns(self):
        start_time = Datetime()
        config = Settings(self.backup.config_file)
        config['remotehost'] = 'remotehost'
        config['repositoryname'] = 'test-repo'
        config['configured'] = True
        config.save()
        with self.assertRaises(NoPatternsError):
            self.backup.start()
        # Check status
        status = self.backup.get_status()
        self.assertTrue(status['lastdate'] > start_time)
        self.assertNotEqual(status['lastdate'], status['lastsuccess'])
        self.assertEqual('FAILURE', status['lastresult'])
        self.assertEqual('include patterns are missing', status['details'])

    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('minarca_client.core.compat.get_ssh', return_value=_ssh)
    @mock.patch('rdiff_backup.Main.Main')
    def test_test_server(self, mock_rdiff_backup, *unused):
        config = Settings(self.backup.config_file)
        config['remotehost'] = 'remotehost'
        config['repositoryname'] = 'test-repo'
        config.save()
        self.backup.test_server()
        # Validate
        mock_rdiff_backup.assert_called_once_with([
            '-v',
            '4',
            '--remote-schema',
            MATCH(_ssh + " -oBatchMode=yes -oPreferredAuthentications=publickey -oUserKnownHostsFile='*known_hosts' -oIdentitiesOnly=yes -i '*id_rsa' %s 'minarca/* rdiff-backup/2.0.0 (*)'"),
            '--test-server',
            'minarca@remotehost::test-repo'])

    @mock.patch('minarca_client.core.Scheduler')
    def test_unlink(self, mock_scheduler):
        # Mock a configuration
        config = Settings(self.backup.config_file)
        config['remotehost'] = 'remotehost'
        config['repositoryname'] = 'test-repo'
        config['configured'] = True
        config.save()
        # Unlink
        self.backup.unlink()
        config = Settings(self.backup.config_file)
        self.assertEqual(False, config['configured'])
        # Validation
        mock_scheduler.return_value.delete.assert_called_once()
