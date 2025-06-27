# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import asyncio
import datetime
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest import mock
from unittest.case import skipIf, skipUnless
from unittest.mock import MagicMock

import responses

from minarca_client.core import Backup, BackupInstance
from minarca_client.core.compat import IS_WINDOWS, ssh_keygen
from minarca_client.core.disk import LocationInfo
from minarca_client.core.exceptions import (
    BackupError,
    HttpAuthenticationError,
    HttpConnectionError,
    HttpInvalidUrlError,
    HttpServerError,
    InvalidRepositoryName,
    NoPatternsError,
    NotConfiguredError,
    NotScheduleError,
    RepositoryNameExistsError,
    UnknownHostException,
)
from minarca_client.core.instance import _sh_quote
from minarca_client.core.pattern import Pattern, Patterns
from minarca_client.core.settings import Datetime, Settings
from minarca_client.tests.test import MATCH

IDENTITY = """[test.minarca.net]:2222 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK/Qng4S5d75rtYxklVdIkPiz4paf2pdnCEshUoailQO root@sestican
[test.minarca.net]:2222 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBCi0uz4rVsLpVl8b6ozYzL+t1Lh9P98a0tY7KqAtzFupjtZivdIYxh6jXPeonYo7egY+mFgMX22Tlrth8woRa2M= root@sestican
[test.minarca.net]:2222 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC+XU4xipQJUKqGshBeCBH7vNfeDgIOXQeaz6Q4S9QbWM39gTUedCfQuabUjXUJafPX8RfEe2xKALaHOdHzT1HYq3GL8oUa4C1J3xkabnZbxA06Ko4Ya31S84G/S+L8kwZ7PmxegZedk6Za49uxBjl/2lBQM4B/BgNccQ9Ifu5Kw4gmU6mfIOZxJ9qx0rF87cXXi5b6o7GMNbK6UViheZvyJQNuR8oYdMEqaVyezJGfSOEFWPm+mQm19Tu4Ad9ElyMyA8SImQshOz7YupEeb26sLvvVwl0EyirMwlI8NIt66DGEy5s2egorL3COB+L0Yp2wjLvzHBMr0Dwb/ZLJfbGR root@sestican
"""

_original_create_subprocess_exec = asyncio.create_subprocess_exec

# A couple of variable to make stuff cross-platform
_echo_foo_cmd = ['cmd.exe', '/c', 'echo foo'] if IS_WINDOWS else ['echo', 'foo']
_exit_1_cmd = ['cmd.exe', '/c', 'exit 1'] if IS_WINDOWS else ['bash', '-c', 'exit 1']
_ssh = 'ssh.exe' if IS_WINDOWS else '/usr/bin/ssh'
_home = 'C:/Users' if IS_WINDOWS else '/home'
_root = 'C:/' if IS_WINDOWS else '/'
_list_increments = '---\n- base: increments.2024-04-12T14-45-49-04-00.dir\n  time: 1712947549\n  type: directory\n- base: increments.2024-04-12T14-45-55-04-00.dir\n  time: 1712947555\n  type: directory\n- base: .\n  time: 1712948833\n  type: directory\n...\n'
_echo_list_increments = (
    ['cmd.exe', '/c', 'echo ' + '&echo '.join(_list_increments.split('\n'))]
    if IS_WINDOWS
    else ['echo', _list_increments]
)
_list_files = '--- Repository file system capabilities ---\n-----------------------------------------------------------------\nDetected abilities for read-only file system\n  Access control lists                         N/A\n  Extended attributes                          N/A\n  Windows access control lists                 N/A\n  Case sensitivity                             On\n  Escape DOS devices                           Off\n  Escape trailing spaces                       Off\n  Mac OS X style resource forks                Off\n  Mac OS X Finder information                  Off\n-----------------------------------------------------------------\n*        Backup: escape_dos_devices = False\n*        Backup: escape_trailing_spaces = True\n*        Enabled use_compatible_timestamps\n.\nhome\nhome/vmtest\nhome/vmtest/Documents\nhome/vmtest/Documents/Work\nhome/vmtest/Documents/Work/Data\nhome/vmtest/Documents/Work/Data/file_example_CSV_5000.csv\nhome/vmtest/Documents/Work/Data/file_example_JSON_1kb.json\nhome/vmtest/Documents/Work/Data/file_example_XLS_5000.xls\nhome/vmtest/Documents/Work/Data/file_example_XML_24kb.xml\nhome/vmtest/Documents/Work/PDF\nhome/vmtest/Documents/Work/PDF/file-example_PDF_1MB.pdf\nhome/vmtest/Documents/Work/PDF/file-example_PDF_500_kB.pdf\nhome/vmtest/Documents/Work/Slideshow\nhome/vmtest/Documents/Work/Slideshow/file_example_PPT_1MB.ppt\nhome/vmtest/Documents/Work/Slideshow/file_example_PPT_250kB (1).ppt\nhome/vmtest/Documents/Work/Slideshow/file_example_PPT_250kB.ppt\nhome/vmtest/Documents/Work/Slideshow/file_example_PPT_500kB.ppt\nhome/vmtest/Documents/Work/file-sample_100kB.doc\nhome/vmtest/Documents/Work/file-sample_100kB.odt\nhome/vmtest/Documents/Work/file-sample_150kB.pdf\nhome/vmtest/Documents/Work/file-sample_1MB.docx\nhome/vmtest/Documents/Work/file-sample_500kB.doc\nhome/vmtest/Documents/Work/file_example_favicon.ico\nhome/vmtest/Documents/Work/zip_2MB.zip\n*        Cleaning up\n'
_echo_list_files = (
    ['cmd.exe', '/c', 'echo ' + '&echo '.join(_list_files.split('\n'))] if IS_WINDOWS else ['echo', _list_files]
)


# FIXME This might not be required anymore since sshkey gen is not called
async def mock_subprocess_link(*args, **kwargs):
    """
    Mock function to avoid calling the real rdiff-backup command. But during linking, we also make call to ssh keygen.
    """

    if len(args) >= 2 and 'rdiff-backup' in args[1]:
        return await _original_create_subprocess_exec(*_echo_foo_cmd, **kwargs)
    return await _original_create_subprocess_exec(*args, **kwargs)


def mock_subprocess_popen(replace_cmd):
    async def mock_call(*args, **kwargs):
        return await _original_create_subprocess_exec(*replace_cmd, *args, **kwargs)

    return mock_call


def remove_readonly(func, path, excinfo):
    """Special handler to remove readonly file on Windows."""
    if excinfo[0].__name__ == 'PermissionError':
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


class TestBackupInstance(unittest.IsolatedAsyncioTestCase):
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

    async def test_configure_remote_with_empty_repository_name(self):
        with self.assertRaises(InvalidRepositoryName):
            await self.backup.configure_remote("http://localhost", "admin", "admin", "")

    async def test_configure_remote_with_invalid_repository_name(self):
        with self.assertRaises(InvalidRepositoryName):
            await self.backup.configure_remote("http://localhost", "admin", "admin", "invalid!?%$/")

    @responses.activate
    async def test_configure_remote_with_existing_repository_name(self):
        # Given an existing repositori on remote server
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

        # When configuring the repo
        # Then error is raised.
        with self.assertRaises(RepositoryNameExistsError):
            await self.backup.configure_remote("http://localhost", "admin", "admin", "coucou")

        # Check with sub folders
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            json={'email': 'admin@example.com', 'username': 'admin', 'repos': [{'name': 'coucou/C'}]},
        )
        with self.assertRaises(RepositoryNameExistsError):
            await self.backup.configure_remote("http://localhost", "admin", "admin", "coucou")

    @responses.activate
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_link)
    async def test_configure_remote_with_existing_repository_name_forced(self, mock_popen):
        # Given an existing repositori on remote server
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            json={
                'email': 'admin@example.com',
                'username': 'admin',
                "role": 10,
                'repos': [{'name': 'coucou', "maxage": 3, "keepdays": 365, "ignore_weekday": [5, 6]}],
            },
        )
        responses.add(
            responses.GET,
            "http://localhost/api/minarca/",
            json={'remotehost': 'remote', 'version': '3.9.0', 'identity': IDENTITY},
        )
        responses.add(responses.POST, "http://localhost/api/currentuser/sshkeys", status=200)

        # When configuring the repo with force (to replace existing repo)
        instance = await self.backup.configure_remote("http://localhost", "admin", "admin", "coucou", force=True)

        # Then instance is configure and settings are initialized with remoter server settings,
        self.assertIsNotNone(instance)
        self.assertEqual(instance.settings.maxage, 3)
        self.assertEqual(instance.settings.keepdays, 365)
        self.assertEqual(instance.settings.ignore_weekday, [5, 6])
        self.assertEqual(instance.settings.remoterole, 10)

    @responses.activate
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_link)
    async def test_configure_remote_with_existing_patterns(self, mock_popen):
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
        self.instance = await self.backup.configure_remote(
            "http://localhost", "admin", "admin", "coucou", instance=self.instance
        )

        # Check calls to web api
        responses.assert_call_count("http://localhost/api/", 1)
        responses.assert_call_count("http://localhost/api/currentuser/", 1)
        responses.assert_call_count("http://localhost/api/minarca/", 1)
        responses.assert_call_count("http://localhost/api/currentuser/sshkeys", 1)

        # Check if rdiff_backup get called.
        mock_popen.assert_called()

        # Then initial pattern are kept.
        patterns = self.instance.patterns
        self.assertEqual(initial_patterns, list(patterns))

    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_link)
    async def test_configure_remote_with_http_invalid_url_error(self, mock_subprocess):
        # Link
        with self.assertRaises(HttpInvalidUrlError):
            await self.backup.configure_remote("not_http_url", "admin", "admin", "coucou")
        mock_subprocess.assert_not_called()

    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_link)
    async def test_configure_remote_with_http_invalid_url_error_2(self, mock_subprocess):
        # Link
        with self.assertRaises(HttpInvalidUrlError):
            await self.backup.configure_remote("ssh://localhost", "admin", "admin", "coucou")
        mock_subprocess.assert_not_called()

    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_link)
    async def test_configure_remote_with_http_connection_error(self, mock_subprocess):
        # Link
        with self.assertRaises(HttpConnectionError):
            await self.backup.configure_remote("http://invalid_host_name", "admin", "admin", "coucou")
        mock_subprocess.assert_not_called()

    @responses.activate
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_link)
    async def test_configure_remote_with_http_authentication_error_401(self, mock_subprocess):
        # Mock authentication fail
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(responses.GET, "http://localhost/api/currentuser/", status=401)

        # Link
        with self.assertRaises(HttpAuthenticationError):
            await self.backup.configure_remote("http://localhost", "admin", "admin", "coucou")
        mock_subprocess.assert_not_called()

    @responses.activate
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_link)
    async def test_configure_remote_with_http_authentication_error_403(self, mock_subprocess):
        # Mock authentication fail
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(responses.GET, "http://localhost/api/currentuser/", status=403)

        # Link
        with self.assertRaises(HttpAuthenticationError):
            await self.backup.configure_remote("http://localhost", "admin", "admin", "coucou")
        mock_subprocess.assert_not_called()

    @responses.activate
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_link)
    async def test_configure_remote_with_http_authentication_error_503(self, mock_subprocess):
        # Mock authentication fail
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(responses.GET, "http://localhost/api/currentuser/", status=503)

        # Link
        with self.assertRaises(HttpServerError):
            await self.backup.configure_remote("http://localhost", "admin", "admin", "coucou")
        mock_subprocess.assert_not_called()

    @responses.activate
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_link)
    async def test_configure_remote(self, mock_popen):
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
        self.instance = await self.backup.configure_remote("http://localhost", "admin", "admin", "coucou")

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

    def test_is_backup_time_with_manual(self):
        # Given a backup with Manual schedule.
        self.instance.settings.schedule = -1
        # Then backup should never start
        self.assertFalse(self.instance.is_backup_time())

    def test_is_running_no_pid(self):
        status = self.instance.status
        status.lastresult = 'SUCCESS'
        self.assertFalse(self.instance.is_running())

    def test_is_running_not_running_pid(self):
        status = self.instance.status
        status.lastresult = 'RUNNING'
        status.pid = 98123456
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

    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_popen(_echo_foo_cmd))
    async def test_pause_with_backup_force(self, unused):
        # Provide default config
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.configured = True
        config.save()
        patterns = self.instance.patterns
        patterns.append(Pattern(True, _home, None))
        patterns.save()
        self.instance._rdiff_backup = mock.AsyncMock()
        # Given a backup pause for 24 hours
        self.instance.pause(24)
        with self.assertRaises(NotScheduleError):
            await self.instance.backup()
        # When running backup with --force
        await self.instance.backup(force=True)
        # Then backup is unpaused
        self.assertIsNone(self.instance.settings.pause_until)

    @mock.patch('minarca_client.core.compat.get_ssh', return_value=_ssh)
    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_popen(_echo_foo_cmd))
    async def test_rdiff_backup(self, mock_rdiff_backup, *unused):
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.save()
        # When calling rdiff_backup with any argument
        await self.instance._rdiff_backup('backup', 'any-argument')
        # Then is trigger a call to rdiff_backup function with the same arguments
        mock_rdiff_backup.assert_called_once_with(
            mock.ANY,
            'rdiff-backup',
            '-v',
            '5',
            'backup',
            'any-argument',
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=mock.ANY,
            creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0,
        )

    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_popen(_exit_1_cmd))
    async def test_rdiff_backup_return_error(self, mock_popen, *unused):
        # Given a configured backup instance
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.save()
        # When executing rdiff-backup return exit-code 1 (see mock)
        # Then an exception is raised.
        with self.assertRaises(BackupError):
            await self.instance._rdiff_backup('backup', 'any-arguments')

    async def test_rdiff_backup_unknown_host(self):
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
            await self.instance.backup()

    async def test_backup_not_configured_remotehost(self):
        config = self.instance.settings
        config.remotehost = ''
        config.repositoryname = 'test-repo'
        config.save()
        self.instance.patterns.extend(Patterns.defaults())
        self.instance.patterns.save()
        # Make the call
        with self.assertRaises(NotConfiguredError):
            await self.instance.backup()

    async def test_backup_not_configured_repositoryname(self):
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = ''
        config.save()
        self.instance.patterns.extend(Patterns.defaults())
        self.instance.patterns.save()
        # Make the call
        with self.assertRaises(NotConfiguredError):
            await self.instance.backup()

    def test_set_schedule(self):
        self.instance.settings.schedule = Settings.HOURLY
        self.assertEqual(Settings.HOURLY, self.instance.settings.schedule)

    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_popen(_echo_foo_cmd))
    async def test_backup(self, mock_popen, *unused):
        start_time = Datetime()
        # Mock call to rdiff-backup
        self.instance._rdiff_backup = mock.AsyncMock()
        # Provide default config
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.configured = True
        config.save()
        patterns = self.instance.patterns
        patterns.append(Pattern(True, _home, None))
        patterns.save()
        await self.instance.backup()
        # Check if rdiff-backup is called.
        if IS_WINDOWS:
            self.instance._rdiff_backup.assert_called_once_with(
                '--remote-schema',
                mock.ANY,
                'backup',
                '--no-hard-links',
                '--exclude-symbolic-links',
                '--create-full-path',
                '--no-resource-forks',
                '--no-compression',
                '--include',
                _home,
                '--exclude',
                'C:/**',
                'C:/',
                'minarca@remotehost::test-repo/C/',
                callback=mock.ANY,
            )
        else:
            self.instance._rdiff_backup.assert_called_once_with(
                '--remote-schema',
                mock.ANY,
                'backup',
                '--exclude-sockets',
                '--no-resource-forks',
                '--no-compression',
                '--include',
                _home,
                '--exclude',
                '/**',
                '/',
                'minarca@remotehost::test-repo/',
                callback=mock.ANY,
            )
        # Check status
        status = self.instance.status
        status.reload()
        self.assertEqual('SUCCESS', status.lastresult)
        self.assertTrue(status.lastsuccess > start_time)
        self.assertEqual(status.lastdate, status.lastsuccess)
        self.assertEqual('', status.details)

    async def test_backup_not_scheduled(self):
        status = self.instance.status
        status.lastsuccess = Datetime()
        with self.assertRaises(NotScheduleError):
            await self.instance.backup()

    async def test_start_without_patterns(self):
        start_time = Datetime()
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.configured = True
        config.save()
        with self.assertRaises(NoPatternsError):
            await self.instance.backup()
        # Check status
        status = self.instance.status
        status.reload()
        self.assertTrue(status.lastdate > start_time)
        self.assertNotEqual(status.lastdate, status.lastsuccess)
        self.assertEqual('FAILURE', status.lastresult)
        self.assertEqual('No files included in backup. Check configuration. (Error: 29)', status.details)

    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('minarca_client.core.compat.get_ssh', return_value=_ssh)
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_popen(_echo_foo_cmd))
    async def test_test_connection(self, mock_rdiff_backup, *unused):
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.save()
        await self.instance.test_connection()
        # Validate
        nul = "" if IS_WINDOWS else " -F /dev/null"
        mock_rdiff_backup.assert_called_once_with(
            mock.ANY,
            'rdiff-backup',
            '-v',
            '5',
            '--remote-schema',
            MATCH(
                _ssh
                + f"{nul} -oBatchMode=yes -oPreferredAuthentications=publickey -oUserKnownHostsFile=*known_hosts? -oIdentitiesOnly=yes -i *id_rsa? %s 'minarca/* rdiff-backup/2.0.0 (*)'"
            ),
            'test',
            'minarca@remotehost::.',
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=mock.ANY,
            creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0,
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
        nul = "" if IS_WINDOWS else " -F /dev/null"
        self.assertEqual(
            value,
            MATCH(
                _ssh
                + f"{nul} -oBatchMode=yes -oPreferredAuthentications=publickey -p 2222 -oUserKnownHostsFile=*known_hosts? -oIdentitiesOnly=yes -i *id_rsa? %s 'minarca/DEV rdiff-backup/2.0.0 (os info)'"
            ),
        )

    @mock.patch('minarca_client.core.disk.get_location_info')
    @mock.patch('minarca_client.core.disk.list_disks')
    async def test_get_disk_usage_with_local(self, mock_list_disk, mock_disk_info):
        # Given a local backup instance
        tempdir = tempfile.mkdtemp(prefix='minarca-client-test')
        dest = os.path.join(tempdir, 'minarca', 'test-repo')
        if IS_WINDOWS:
            mountpoint, relpath = os.path.splitdrive(dest)
        else:
            mountpoint, relpath = dest[0], dest[1:]
        my_disk_info = LocationInfo(
            mountpoint=Path(mountpoint),
            relpath=Path(relpath),
            caption='SAMSUNG MZVL2512HDJD-00BL2',
            free=14288068608,
            used=48573071360,
            size=66260148224,
            fstype='ext4',
            device_type=LocationInfo.FIXED,
        )
        mock_list_disk.return_value = [Path(mountpoint)]
        mock_disk_info.return_value = my_disk_info
        try:
            os.makedirs(dest)
            self.instance = await self.backup.configure_local(dest, repositoryname='test-repo')
            # When get getting disk usage
            used, size = await self.instance.get_disk_usage()
            # Then disk usage is returned
            self.assertTrue(used)
            self.assertTrue(size)
        finally:
            shutil.rmtree(tempdir, onerror=remove_readonly)

    @responses.activate
    async def test_get_disk_usage_with_remote(self):
        # Mock some https stuff
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            json={
                'email': 'admin@example.com',
                'username': 'admin',
                'repos': [{'name': 'test-repo'}],
                'disk_quota': 1234,
                'disk_usage': 123,
            },
        )
        # Given a remote backup instance
        ssh_keygen(self.instance.public_key_file, self.instance.private_key_file)
        config = self.instance.settings
        config.remoteurl = 'http://localhost/'
        config.username = 'admin'
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.save()
        # When get getting disk usage
        used, size = await self.instance.get_disk_usage()
        # Then disk usage is returned
        self.assertTrue(used)
        self.assertTrue(size)

    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_popen(_echo_foo_cmd))
    async def test_restore(self, mock_popen, *unused):
        start_time = Datetime()
        # Mock call to rdiff-backup
        self.instance._rdiff_backup = mock.AsyncMock()
        # Provide default config
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.configured = True
        config.save()
        path_to_restore = 'C:/path/to/file' if IS_WINDOWS else '/path/to/file'
        destination = 'C:\\tmp' if IS_WINDOWS else '/tmp'
        await self.instance.restore(restore_time='1712944964', paths=[path_to_restore], destination=destination)
        # Check if rdiff-backup is called.
        if IS_WINDOWS:
            self.instance._rdiff_backup.assert_called_once_with(
                '--force',
                '--remote-schema',
                mock.ANY,
                'restore',
                '--at',
                '1712944964',
                'minarca@remotehost::test-repo/C/path/to/file',
                'C:\\tmp\\file',
                callback=mock.ANY,
            )
        else:
            self.instance._rdiff_backup.assert_called_once_with(
                '--force',
                '--remote-schema',
                mock.ANY,
                'restore',
                '--at',
                '1712944964',
                'minarca@remotehost::test-repo/path/to/file',
                '/tmp/file',
                callback=mock.ANY,
            )
        # Check status
        status = self.instance.status
        status.reload()
        self.assertEqual('SUCCESS', status.lastresult)
        self.assertTrue(status.lastsuccess > start_time)
        self.assertEqual(status.lastdate, status.lastsuccess)
        self.assertEqual('', status.details)
        self.assertEqual('restore', status.action)

    @responses.activate
    async def test_save_remote_settings(self):
        # Given a server with a remote backup
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            json={
                'email': 'admin@example.com',
                'username': 'admin',
                'repos': [{'name': 'test-repo'}],
                'disk_quota': 1234,
                'disk_usage': 123,
            },
        )
        responses.add(
            responses.POST,
            "http://localhost/api/currentuser/repos/test-repo",
        )
        # Given a remote backup instance
        ssh_keygen(self.instance.public_key_file, self.instance.private_key_file)
        config = self.instance.settings
        config.remoteurl = 'http://localhost/'
        config.username = 'admin'
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.save()
        # When updating the settings and saving them remotely
        config.keepdays = 15
        config.save()
        await self.instance.save_remote_settings()
        # Then the settings are push to the remote server.
        responses.assert_call_count("http://localhost/api/currentuser/repos/test-repo", 1)

    @responses.activate
    async def test_load_remote_settings(self):
        # Given a server with a remote backup
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            json={
                'email': 'admin@example.com',
                'username': 'admin',
                'repos': [{'name': 'test-repo'}],
                'disk_quota': 1234,
                'disk_usage': 123,
            },
        )
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/repos/test-repo",
            json={'maxage': 12, 'keepdays': 34, 'ignore_weekday': [5, 6]},
        )
        # Given a remote backup instance
        ssh_keygen(self.instance.public_key_file, self.instance.private_key_file)
        config = self.instance.settings
        config.remoteurl = 'http://localhost/'
        config.username = 'admin'
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.save()
        # When loading the settings
        await self.instance.load_remote_settings()
        # Then the settings are push to the remote server.
        responses.assert_call_count("http://localhost/api/currentuser/repos/test-repo", 1)
        self.assertEqual(config.maxage, 12)
        self.assertEqual(config.keepdays, 34)
        self.assertEqual(config.ignore_weekday, [5, 6])

    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_popen(_echo_list_increments))
    async def test_list_increments(self, mock_popen, *unused):
        # Given a backup settings
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.configured = True
        config.save()
        self.instance.patterns.extend(Patterns.defaults())
        self.instance.patterns.save()
        # When querying the list of increments
        data = await self.instance.list_increments()
        # Then list of increment is returned
        self.assertEqual(
            data,
            [
                datetime.datetime.fromtimestamp(1712947549, tz=datetime.timezone.utc),
                datetime.datetime.fromtimestamp(1712947555, tz=datetime.timezone.utc),
                datetime.datetime.fromtimestamp(1712948833, tz=datetime.timezone.utc),
            ],
        )
        # Then rdiff-backup command line is executed
        mock_popen.assert_called_once_with(
            mock.ANY,
            'rdiff-backup',
            '-v',
            '5',
            '--remote-schema',
            mock.ANY,
            '--api-version',
            '201',
            '--parsable-output',
            'list',
            'increments',
            'minarca@remotehost::test-repo/C/' if IS_WINDOWS else 'minarca@remotehost::test-repo/',
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=mock.ANY,
            creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0,
        )

    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_popen(_echo_list_files))
    async def test_list_files(self, mock_popen, *unused):
        # Given a backup settings
        config = self.instance.settings
        config.remotehost = 'remotehost'
        config.repositoryname = 'test-repo'
        config.configured = True
        config.save()
        self.instance.patterns.extend(Patterns.defaults())
        self.instance.patterns.save()
        # When querying the list of increments
        data = await self.instance.list_files(datetime.datetime.fromtimestamp(1713195267, tz=datetime.timezone.utc))
        # Then list of increment is returned
        if IS_WINDOWS:
            self.assertEqual(
                data,
                [
                    'C:/home',
                    'C:/home/vmtest',
                    'C:/home/vmtest/Documents',
                    'C:/home/vmtest/Documents/Work',
                    'C:/home/vmtest/Documents/Work/Data',
                    'C:/home/vmtest/Documents/Work/Data/file_example_CSV_5000.csv',
                    'C:/home/vmtest/Documents/Work/Data/file_example_JSON_1kb.json',
                    'C:/home/vmtest/Documents/Work/Data/file_example_XLS_5000.xls',
                    'C:/home/vmtest/Documents/Work/Data/file_example_XML_24kb.xml',
                    'C:/home/vmtest/Documents/Work/PDF',
                    'C:/home/vmtest/Documents/Work/PDF/file-example_PDF_1MB.pdf',
                    'C:/home/vmtest/Documents/Work/PDF/file-example_PDF_500_kB.pdf',
                    'C:/home/vmtest/Documents/Work/Slideshow',
                    'C:/home/vmtest/Documents/Work/Slideshow/file_example_PPT_1MB.ppt',
                    'C:/home/vmtest/Documents/Work/Slideshow/file_example_PPT_250kB (1).ppt',
                    'C:/home/vmtest/Documents/Work/Slideshow/file_example_PPT_250kB.ppt',
                    'C:/home/vmtest/Documents/Work/Slideshow/file_example_PPT_500kB.ppt',
                    'C:/home/vmtest/Documents/Work/file-sample_100kB.doc',
                    'C:/home/vmtest/Documents/Work/file-sample_100kB.odt',
                    'C:/home/vmtest/Documents/Work/file-sample_150kB.pdf',
                    'C:/home/vmtest/Documents/Work/file-sample_1MB.docx',
                    'C:/home/vmtest/Documents/Work/file-sample_500kB.doc',
                    'C:/home/vmtest/Documents/Work/file_example_favicon.ico',
                    'C:/home/vmtest/Documents/Work/zip_2MB.zip',
                ],
            )
        else:
            self.assertEqual(
                data,
                [
                    '/home',
                    '/home/vmtest',
                    '/home/vmtest/Documents',
                    '/home/vmtest/Documents/Work',
                    '/home/vmtest/Documents/Work/Data',
                    '/home/vmtest/Documents/Work/Data/file_example_CSV_5000.csv',
                    '/home/vmtest/Documents/Work/Data/file_example_JSON_1kb.json',
                    '/home/vmtest/Documents/Work/Data/file_example_XLS_5000.xls',
                    '/home/vmtest/Documents/Work/Data/file_example_XML_24kb.xml',
                    '/home/vmtest/Documents/Work/PDF',
                    '/home/vmtest/Documents/Work/PDF/file-example_PDF_1MB.pdf',
                    '/home/vmtest/Documents/Work/PDF/file-example_PDF_500_kB.pdf',
                    '/home/vmtest/Documents/Work/Slideshow',
                    '/home/vmtest/Documents/Work/Slideshow/file_example_PPT_1MB.ppt',
                    '/home/vmtest/Documents/Work/Slideshow/file_example_PPT_250kB (1).ppt',
                    '/home/vmtest/Documents/Work/Slideshow/file_example_PPT_250kB.ppt',
                    '/home/vmtest/Documents/Work/Slideshow/file_example_PPT_500kB.ppt',
                    '/home/vmtest/Documents/Work/file-sample_100kB.doc',
                    '/home/vmtest/Documents/Work/file-sample_100kB.odt',
                    '/home/vmtest/Documents/Work/file-sample_150kB.pdf',
                    '/home/vmtest/Documents/Work/file-sample_1MB.docx',
                    '/home/vmtest/Documents/Work/file-sample_500kB.doc',
                    '/home/vmtest/Documents/Work/file_example_favicon.ico',
                    '/home/vmtest/Documents/Work/zip_2MB.zip',
                ],
            )
        # Then rdiff-backup command line is executed
        mock_popen.assert_called_once_with(
            mock.ANY,
            'rdiff-backup',
            '-v',
            '5',
            '--remote-schema',
            mock.ANY,
            '--api-version',
            '201',
            '--parsable-output',
            'list',
            'files',
            '--at',
            '1713195267',
            'minarca@remotehost::test-repo/C/' if IS_WINDOWS else 'minarca@remotehost::test-repo/',
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=mock.ANY,
            creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0,
        )

    @mock.patch('minarca_client.core.status.send_notification', return_value='12345')
    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_popen(_exit_1_cmd))
    async def test_backup_send_notification(self, mock_popen, mock_get_user_agent, mock_send_notification):
        # Given a repository defined with a maxage value.
        settings = self.instance.settings
        settings.remotehost = 'remotehost'
        settings.repositoryname = 'test-repo'
        settings.configured = True
        settings.maxage = 3
        settings.save()
        # Given a repository configured with some patterns.
        patterns = self.instance.patterns
        patterns.append(Pattern(True, _home, None))
        patterns.save()
        # When backup fail.
        with self.assertRaises(BackupError):
            await self.instance.backup()
        self.instance.status.reload()
        self.assertEqual('FAILURE', self.instance.status.lastresult)
        # Then notification was raised to user.
        mock_send_notification.assert_called_once_with(title='Your backup is outdated', body=mock.ANY, replace_id=None)

    @mock.patch('minarca_client.core.status.clear_notification', return_value='12345')
    @mock.patch('minarca_client.core.compat.get_user_agent', return_value='minarca/DEV rdiff-backup/2.0.0 (os info)')
    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_popen(_echo_foo_cmd))
    async def test_backup_clear_notification_time(self, mock_popen, mock_get_user_agent, mock_clear_notification):
        # Given a repository defined with a maxage value.
        settings = self.instance.settings
        settings.remotehost = 'remotehost'
        settings.repositoryname = 'test-repo'
        settings.configured = True
        settings.maxage = 3
        settings.save()
        self.instance.status.lastnotificationid = 'previous-id'
        # Given a repository configured with some patterns.
        patterns = self.instance.patterns
        patterns.append(Pattern(True, _home, None))
        patterns.save()
        # When backup success.
        await self.instance.backup()
        self.instance.status.reload()
        self.assertEqual('SUCCESS', self.instance.status.lastresult)
        # Then notification was raised to user.
        mock_clear_notification.assert_called_once_with('previous-id')

    async def test_local_backup(self):
        # Given a backup with local destination
        tempdir = tempfile.mkdtemp(prefix='minarca-client-test')
        try:
            self.instance = await self.backup.configure_local(tempdir, repositoryname='test-repo')
            patterns = self.instance.patterns
            patterns.clear()
            patterns.append(Pattern(True, self.tmp.name, None))
            patterns.save()
            # Then backup is created in pause mode.
            self.assertIsNotNone(self.instance.settings.pause_until)
            # when running backup
            await self.instance.backup(force=True)
            # then a backup get created
            if IS_WINDOWS:
                drive = os.path.splitdrive(tempdir)[0][0]
                self.assertTrue(os.path.isdir(os.path.join(tempdir, drive, 'rdiff-backup-data')))
            else:
                self.assertTrue(os.path.isdir(os.path.join(tempdir, 'rdiff-backup-data')))
        finally:
            shutil.rmtree(tempdir, onerror=remove_readonly)

    async def test_local_backup_with_special_encoding(self):
        # Given a backup with local destination
        tempdir = tempfile.mkdtemp(prefix='minarca-client-test')
        try:
            self.instance = await self.backup.configure_local(tempdir, repositoryname='test-repo')
            patterns = self.instance.patterns
            patterns.clear()
            patterns.append(Pattern(True, os.path.realpath(self.tmp.name), None))
            patterns.save()
            # Create a file with special char (Euro sign €)
            Path(self.tmp.name, 'my \u20ac income').write_text('some data')
            # Then backup is created in pause mode.
            self.assertIsNotNone(self.instance.settings.pause_until)
            # when running backup
            await self.instance.backup(force=True)
            # then a backup get created
            if IS_WINDOWS:
                drive = os.path.splitdrive(tempdir)[0][0]
                self.assertTrue(os.path.isdir(os.path.join(tempdir, drive, 'rdiff-backup-data')))
            else:
                self.assertTrue(os.path.isdir(os.path.join(tempdir, 'rdiff-backup-data')))
            # then backup logs contains our filename with special char.
            self.assertIn('my \u20ac income', Path(self.instance.backup_log_file).read_text(encoding='utf-8'))
        finally:
            shutil.rmtree(tempdir, onerror=remove_readonly)

    @mock.patch('asyncio.create_subprocess_exec', side_effect=mock_subprocess_popen(_echo_foo_cmd))
    async def test_local_backup_with_keepdays(self, mock_popen):
        # Given a backup with local destination
        tempdir = tempfile.mkdtemp(prefix='minarca-client-test')
        try:
            self.instance = await self.backup.configure_local(tempdir, repositoryname='test-repo')
            self.instance.settings.keepdays = 3
            patterns = self.instance.patterns
            patterns.clear()
            patterns.append(Pattern(True, self.tmp.name, None))
            patterns.save()
            # when running backup
            await self.instance.backup(force=True)
            # then rdiff-backup is called twice.
            self.assertEqual(2, mock_popen.call_count)
            # then last call should remove increments
            mock_popen.assert_called_with(
                mock.ANY,
                'rdiff-backup',
                '-v',
                '5',
                '--force',
                'remove',
                'increments',
                '--older-than',
                '3D',
                mock.ANY,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=mock.ANY,
                creationflags=subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0,
            )
        finally:
            shutil.rmtree(tempdir, onerror=remove_readonly)

    async def test_configure_local_with_existing_repository_name(self):
        # Given a local backup
        tempdir = tempfile.mkdtemp(prefix='minarca-client-test')
        try:
            self.instance = await self.backup.configure_local(tempdir, repositoryname='test-repo')
            self.instance.patterns.clear()
            self.instance.patterns.append(Pattern(True, self.tmp.name, None))
            self.instance.patterns.save()
            await self.instance.backup(force=True)
            self.instance.forget()

            # When trying to configure a local backup at the same destination
            # Then an exception is raised
            with self.assertRaises(RepositoryNameExistsError):
                self.instance = await self.backup.configure_local(tempdir, repositoryname='test-repo')
        finally:
            shutil.rmtree(tempdir, onerror=remove_readonly)

    async def test_configure_local_with_existing_repository_name_forced(self):
        # Given a local backup
        tempdir = tempfile.mkdtemp(prefix='minarca-client-test')
        try:
            self.instance = await self.backup.configure_local(tempdir, repositoryname='test-repo')
            self.instance.patterns.clear()
            self.instance.patterns.append(Pattern(True, self.tmp.name, None))
            self.instance.patterns.save()
            await self.instance.backup(force=True)
            self.instance.forget()
            # When trying to configure a local backup at the same destination with Force mode
            self.instance = await self.backup.configure_local(tempdir, repositoryname='test-repo', force=True)
            # Then the backup get configured.
            # Then backup is paused
            self.assertIsNotNone(self.instance.settings.pause_until)
        finally:
            shutil.rmtree(tempdir, onerror=remove_readonly)

    def test_sh_quote(self):
        self.assertEqual(_sh_quote(['a', 'b', 'c']), "a b c")
        self.assertEqual(_sh_quote(['path with space', 'b', 'c']), '"path with space" b c')

    async def test_pre_post_command(self):
        # Given a backup with local destination
        tempdir = tempfile.mkdtemp(prefix='minarca-client-test')
        pre_file = os.path.join(self.tmp.name, 'foo.txt')
        post_file = os.path.join(self.tmp.name, 'bar.txt')
        try:
            # Given backup with pre/post hook command
            self.instance = await self.backup.configure_local(tempdir, repositoryname='test-repo')
            self.instance.settings.pre_hook_command = "echo foo > %s" % pre_file
            self.instance.settings.post_hook_command = "echo bar > %s" % post_file
            self.instance.settings.ignore_hook_errors = True
            self.instance.settings.save()
            # Given a backup with patterns
            patterns = self.instance.patterns
            patterns.clear()
            patterns.append(Pattern(True, self.tmp.name, None))
            patterns.save()
            # When running backup
            await self.instance.backup(force=True)
            # Then pre/post command was executed
            self.assertTrue(os.path.isfile(pre_file))
            self.assertTrue(os.path.isfile(post_file))
        finally:
            shutil.rmtree(tempdir, onerror=remove_readonly)
