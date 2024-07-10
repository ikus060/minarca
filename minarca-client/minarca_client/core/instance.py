# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import asyncio
import contextlib
import datetime
import functools
import logging
import os
import re
import stat
import subprocess
import tempfile
import time

import psutil
import yaml
from requests.exceptions import ConnectionError, HTTPError, InvalidSchema, MissingSchema
from tzlocal import get_localzone

from minarca_client.core import compat
from minarca_client.core.compat import IS_WINDOWS, detach_call, file_read, flush, get_minarca_exe
from minarca_client.core.config import Datetime, Patterns, Settings, Status
from minarca_client.core.disk import get_location_info, list_disks
from minarca_client.core.exceptions import (
    CaptureException,
    HttpAuthenticationError,
    HttpConnectionError,
    HttpInvalidUrlError,
    HttpServerError,
    LocalDestinationNotFound,
    NoPatternsError,
    NotConfiguredError,
    NotRunningError,
    NotScheduleError,
    RdiffBackupException,
    RdiffBackupExitError,
    RemoteRepositoryNotFound,
    RunningError,
)
from minarca_client.core.minarcaid import ssh_keygen
from minarca_client.core.notification import clear_notification, send_notification
from minarca_client.core.rdiffweb import Rdiffweb
from minarca_client.locale import _

logger = logging.getLogger(__name__)


def _sh_quote(args):
    """
    Used for logging only. Escape command line.
    """
    value = ''
    for a in args:
        if value:
            value += " "
        if " " in a or "*" in a or "?" in a:
            value += '"%s"' % a.replace('"', '\"')
        else:
            value += a
    return value


def _escape_path(path):
    """
    Used to escape the ssh.exe path that contains spaces.
    On Windows we use DOS compatible file path.
    On other platform, we escape the spaces.
    """
    if ' ' not in path:
        return path
    if IS_WINDOWS:
        import win32api

        return win32api.GetShortPathName(path)
    else:
        return "'" + path + "'"


def handle_http_errors(func):
    """
    Decorator to handle HTTP exception raised when calling rdiffweb server.
    """

    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except ConnectionError:
            # Raised with invalid url or port
            raise HttpConnectionError(self.settings.remoteurl)
        except (MissingSchema, InvalidSchema):
            raise HttpInvalidUrlError(self.settings.remoteurl)
        except HTTPError as e:
            # Raise for invalid status code.
            if e.response.status_code in [401, 403]:
                raise HttpAuthenticationError(e)
            # Special case to extract error message from HTML body.
            server_error = HttpServerError(e)
            if e.response.status_code == 400 and e.response.text.startswith('<'):
                m = re.search(r'<p>(.*)</p>', e.response.text)
                if m and m[1]:
                    server_error.message = m[1]
            raise server_error

    return wrapper


class _Collector:
    _writing = False
    file = None

    def __init__(self, start_marker, end_marker) -> None:
        assert start_marker
        assert end_marker
        # Handle line separator
        self._start_marker = start_marker + os.linesep
        self._end_marker = end_marker + os.linesep

    def write(self, data):
        assert self.file
        if data == self._start_marker:
            self._writing = True
        elif data == self._end_marker:
            self._writing = False
        if self._writing:
            self.file.write(data)
        else:
            logger.debug(data.rstrip('\r\n'))

    def flush(self):
        # No need to flush on every call.
        pass

    def close(self):
        assert self.file
        self.file.close()

    def __enter__(self):
        self.file = tempfile.TemporaryFile(mode='w+', errors='replace', newline='')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        self.file = None


@contextlib.contextmanager
def safe_keepawake():
    """Safe implementation of keepawake"""
    try:
        from wakepy import set_keepawake

        set_keepawake(keep_screen_awake=False)
    except ImportError:
        # When not supported, an import error is raised
        logger.info("keep awake not supported on this system")
    except Exception:
        logger.warning("failed to set keep awake", exc_info=1)
    yield
    try:
        from wakepy import set_keepawake, unset_keepawake

        unset_keepawake()
    except ImportError:
        pass
    except Exception:
        logger.warning("failed to unset keep awake", exc_info=1)


class UpdateNotification:
    """
    Handle update of notification when backup is success or fail.
    """

    def __init__(self, instance):
        assert instance
        self.instance = instance

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        status = self.instance.status
        settings = self.instance.settings
        if exc_type is None:
            # Backup is successful
            # clear previous notification (if any).
            notification_id = status.lastnotificationid
            if notification_id:
                logger.debug("clear previous notification %s", notification_id)
                try:
                    clear_notification(notification_id)
                except Exception:
                    pass
                status.lastnotificationid = None
        else:
            # Backup failed
            if self.is_notification_time():
                # show notification if inactivity period is reached.
                previous_id = status.lastnotificationid
                logger.info("create or replace notification: %s", previous_id)
                maxage = settings.maxage
                try:
                    notification_id = send_notification(
                        title=_('Your backup is outdated'),
                        body=_(
                            'Your backup %s is outdated by over %s days. Please plug in your local device and run the backup.'
                        )
                        % (settings.repositoryname, maxage),
                        replace_id=previous_id,
                    )
                    status.lastnotificationid = notification_id
                    status.lastnotificationdate = Datetime()
                except Exception:
                    logger.warn("problem while sending new notification", exc_info=1)
        status.save()

    def is_notification_time(self):
        """
        Return true if the application should raise a notification.
        """
        status = self.instance.status
        settings = self.instance.settings
        # Do not notify if max age is not defined.
        if settings.maxage is None or settings.maxage <= 0:
            return False
        # Only notify every 24 hrs.
        if status.lastnotificationdate and Datetime() - status.lastnotificationdate < datetime.timedelta(days=1):
            return False
        # Notify if last backup never occured.
        if status.lastsuccess is None:
            return True
        # Notify if reaching maxage.
        return Datetime() - status.lastsuccess > datetime.timedelta(days=settings.maxage)


class UpdateStatus:
    """
    Update the status while the backup is running.
    """

    def __init__(self, status, action='backup'):
        assert action in ['backup', 'restore']
        self.status = status
        self.action = action
        self.running = False

    def _write_status(self):
        self.status.pid = os.getpid()
        self.status.lastresult = 'RUNNING'
        self.status.lastdate = Datetime()
        self.status.details = ''
        self.status.action = self.action
        self.status.save()

    async def _task(self):
        """Update the status file continiously with new data."""
        while self.running:
            await asyncio.sleep(Status.RUNNING_DELAY - 1)
            self._write_status()

    async def __aenter__(self):
        self.running = True
        # Start the process by writing a file time to the file
        logger.info("%s START", self.action)
        self._write_status()
        self.task = asyncio.create_task(self._task())

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        await self.task
        if exc_type is None:
            logger.info("%s SUCCESS", self.action)
            with self.status as t:
                t.lastresult = 'SUCCESS'
                t.lastsuccess = Datetime()
                t.lastdate = self.status.lastsuccess
                t.details = ''
        else:
            logger.error("%s FAILED", self.action)
            with self.status as t:
                t.lastresult = 'FAILURE'
                t.lastdate = Datetime()
                t.details = str(exc_val)


class BackupInstance:
    def __init__(self, id):
        """
        Create a new minarca backup backup.
        """
        assert (isinstance(id, int) and id >= 0) or isinstance(id, str)
        self.id = id
        # Get file location.
        self.public_key_file = os.path.join(compat.get_config_home(), "id_rsa%s.pub" % id)
        self.private_key_file = os.path.join(compat.get_config_home(), "id_rsa%s" % id)
        self.known_hosts = os.path.join(compat.get_config_home(), "known_hosts%s" % id)
        self.config_file = os.path.join(compat.get_config_home(), "minarca%s.properties" % id)
        self.patterns_file = os.path.join(compat.get_config_home(), "patterns%s" % id)
        self.status_file = os.path.join(compat.get_data_home(), 'status%s.properties' % id)
        self.backup_log_file = os.path.join(compat.get_data_home(), 'backup%s.log' % id)
        self.restore_log_file = os.path.join(compat.get_data_home(), 'restore%s.log' % id)
        # Create wrapper arround config files.
        self.patterns = Patterns(self.patterns_file)
        self.status = Status(self.status_file)
        self.settings = Settings(self.config_file)

    async def backup(self, force=False):
        """
        Execute the rdiff-backup process.
        Set `force` to True to run backup process event when it's not the time to run.
        """
        # Check if it's time to run a backup
        if self.is_running():
            raise RunningError()
        if not force and not self.is_backup_time():
            raise NotScheduleError()

        # Clear pause if backup started with force
        if self.settings.pause_until is not None:
            self.settings.pause_until = None

        # Start a thread to update backup status.
        with safe_keepawake():
            with UpdateNotification(instance=self):
                async with UpdateStatus(status=self.status):
                    with open(self.backup_log_file, 'w', errors='replace', newline='') as log_file:
                        # Check patterns
                        patterns = self.patterns
                        if not patterns:
                            raise NoPatternsError()

                        # On Windows operating system, the computer may have multiple Root
                        # (C:\, D:\, etc). To support this scenario, we need to run
                        # rdiff-backup multiple time on the same computer. Once for each Root
                        # to be backup (if required).
                        for drive, patterns in patterns.group_by_roots():
                            args = []
                            # If required add remote-schema to define how to connect to SSH Server
                            if self.is_remote():
                                args.append("--remote-schema")
                                args.append(self._remote_schema())
                            args.append("backup")
                            if IS_WINDOWS:
                                args.extend(
                                    [
                                        "--no-hard-links",
                                        "--exclude-symbolic-links",
                                        "--create-full-path",
                                    ]
                                )
                            else:
                                args.append("--exclude-sockets")
                            args.append("--no-compression")
                            # Add Include exclude patterns. Those are already sorted.
                            for p in patterns:
                                args.append("--include" if p.include else "--exclude")
                                args.append(p.pattern)
                            # Exclude everything else
                            args.extend(["--exclude", "%s**" % drive])
                            # Call rdiff-backup
                            dest = self._backup_path(drive)
                            await self._rdiff_backup(*args, drive, dest, log_file=log_file)
                            # For local disk, make sure to "flush" disk cache
                            if self.is_local():
                                logger.info("flush changes to disk")
                                flush(dest)

                            # For local disk, we need to manage the retention period too.
                            if self.is_local() and self.settings.keepdays and self.settings.keepdays > 0:
                                await self._rdiff_backup(
                                    '--force',
                                    'remove',
                                    'increments',
                                    '--older-than',
                                    '%sD' % self.settings.keepdays,
                                    dest,
                                    log_file=log_file,
                                )

    def get_repo_url(self, page="browse"):
        """
        Return a URL to browse data. Either https:// or file://
        """
        if self.is_remote():
            assert page in ['browse', 'settings']
            if IS_WINDOWS:
                # On Windows, we append a drive letter.
                drive_letter, unused = next(self.patterns.group_by_roots(), (None, []))
                if not drive_letter:
                    return self.settings.remoteurl
                repo = self.settings.repositoryname + '/' + drive_letter[0]
            else:
                repo = self.settings.repositoryname
            return "%s/%s/%s/%s" % (self.settings.remoteurl, page, self.settings.username, repo)
        else:
            assert page in ['browse']
            return "file://%s" % self._backup_path(None)

    def get_help_url(self):
        """
        Return a URL to help.
        """
        if self.settings.remoteurl:
            return "%s/help" % (self.settings.remoteurl,)

    def is_backup_time(self):
        """
        Check if it's time to backup.
        """
        # Check if paused.
        pause_until = self.settings.pause_until
        if pause_until and Datetime() < pause_until:
            return False
        # Check if backup ever ran.
        lastsuccess = self.status.lastsuccess
        if lastsuccess is None:
            return True
        # Check if interval passed
        interval = datetime.timedelta(hours=self.settings.schedule * 98.0 / 100)
        time_since_last_backup = Datetime() - lastsuccess
        return interval < time_since_last_backup

    def is_running(self):
        """
        Return true if a backup is running.
        """
        # Check status for running backup.
        return self.status.current_status == 'RUNNING'

    def is_local(self):
        return bool(self.settings.localuuid and self.settings.localrelpath)

    def is_remote(self):
        return bool(self.settings.remotehost and self.settings.repositoryname)

    def pause(self, delay):
        """
        Used to prevent execution of backup for a given periode of time in hours.
        """
        assert isinstance(delay, int)
        # Store absolute time for calculation.
        if delay > 0:
            self.settings.pause_until = Datetime() + datetime.timedelta(hours=delay)
        else:
            self.settings.pause_until = None
        self.settings.save()

    async def _push_identity(self, conn, name):
        # Check if ssh keys exists, if not generate new keys.
        if not os.path.exists(self.public_key_file) and not os.path.exists(self.private_key_file):
            logger.info(_('generating identity'))
            ssh_keygen(self.public_key_file, self.private_key_file)

        # Push SSH Keys to Minarca server
        try:
            with open(self.public_key_file) as f:
                logger.info(_('exchanging identity with minarca server'))
                await asyncio.get_running_loop().run_in_executor(None, conn.post_ssh_key, name, f.read())
        except Exception:
            # Probably a duplicate SSH Key, let generate new identity
            logger.info(_('generating new identity'))
            ssh_keygen(self.public_key_file, self.private_key_file)
            # Publish new identify
            with open(self.public_key_file) as f:
                logger.info(_('exchanging new identity with minarca server'))
                await asyncio.get_running_loop().run_in_executor(None, conn.post_ssh_key, name, f.read())

    async def _rdiff_backup(self, *extra_args, log_file=None):
        """
        Make a call to rdiff-backup executable
        """
        # base command line
        args = ["rdiff-backup", "-v", "5"]
        args.extend(extra_args)

        # Execute the command line.
        capture = CaptureException()
        logger.info(_('executing command: %s') % _sh_quote(args))
        try:
            process = await asyncio.create_subprocess_exec(
                get_minarca_exe(),
                *args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            # Stream the output of rdiff-backup to log file and exception capture.
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                line = line.decode('utf-8', errors='replace')
                if log_file:
                    log_file.write(line)
                    log_file.flush()
                else:
                    logger.debug(line.rstrip('\r\n'))
                capture.parse(line)
            # Check return code
            exit_code = await process.wait()
        except Exception as e:
            if capture.exception:
                raise capture.exception
            logger.info('process terminated with an exception', exc_info=1)
            raise RdiffBackupException(str(e))
        else:
            if capture.exception:
                raise capture.exception
            if exit_code not in [0, 2, 8]:
                raise RdiffBackupExitError(exit_code)

    async def restore(self, restore_time=None, paths=[], destination=None):
        """
        Used to run a complete restore of data backup for the given date or latest date is not defined.
        """
        assert restore_time is None or isinstance(restore_time, str)
        assert isinstance(paths, list)
        assert destination is None or isinstance(destination, str)
        if self.is_running():
            raise RunningError()
        status = Status(self.status_file)
        with safe_keepawake():
            async with UpdateStatus(status=status, action='restore'):
                with open(self.restore_log_file, 'w', errors='replace', newline='') as log_file:
                    # Loop on each pattern to be restored and execute rdiff-backup.
                    for path in paths:
                        if destination:
                            # Restore into different location
                            final_destination = os.path.join(destination, os.path.basename(path))
                        else:
                            # Restore in place
                            final_destination = path
                        # Force is required to replace folder
                        args = ["--force"]
                        # If required add remote-schema to define how to connect to SSH Server
                        if self.is_remote():
                            args.append("--remote-schema")
                            args.append(self._remote_schema())
                        args += ["restore", "--at", restore_time or "now", self._backup_path(path), final_destination]
                        # FIXME For full restore we should add exclude pattern, but rdiff-backup raise an error.
                        await self._rdiff_backup(
                            *args,
                            log_file=log_file,
                        )

    def start_backup(self, force=False):
        """
        Trigger execution of minarca in detach mode.
        """
        args = [get_minarca_exe(), 'backup']
        if force:
            args += ['--force']
        args += ['--limit', str(self.id)]
        child = detach_call(args)
        logger.info('subprocess %s started' % child.pid)

    def start_restore(self, restore_time=None, paths=[], destination=None):
        assert restore_time is None or isinstance(restore_time, int)
        assert isinstance(paths, (list, str))
        if isinstance(paths, str):
            paths = [paths]
        assert paths
        assert destination is None or isinstance(destination, str)

        args = [get_minarca_exe(), 'restore']
        args += ['--force']
        args += ['--limit', str(self.id)]
        if restore_time:
            args += ['--restore-time', str(restore_time)]
        if destination:
            args += ['--destination', str(destination)]
        args += paths
        child = detach_call(args)
        logger.info('subprocess %s started' % child.pid)

    def stop(self):
        """
        Stop the running backup process.
        """
        # Check status for running backup.
        if not self.is_running():
            raise NotRunningError()
        # Get pid and checkif process is running.
        pid = self.status.pid
        p = psutil.Process(pid)
        if not p.is_running():
            raise NotRunningError()
        # Send appropriate signal
        logger.info('terminating process %s' % pid)
        try:
            # To terminate the backup, the best is to kill the SSH connection.
            for child in p.children(recursive=True):
                if 'ssh.exe' in child.name() or 'ssh' in child.name():
                    child.terminate()
            p.terminate()
        except SystemError:
            logger.warning('error trying to stop minarca', exc_info=1)
        # Wait until process get killed
        count = 1
        while p.is_running() and count < 10:
            time.sleep(0.1)
            count += 1
        # Replace status by INTERRUPT
        logger.info('process interrupted successfully')
        with self.status as t:
            t.lastresult = 'INTERRUPT'
            t.lastdate = Datetime()
            t.details = ''

    async def test_connection(self):
        """
        Check connectivity to the remote server or local disk using rdiff-backup.
        """

        if self.is_remote():
            # Since v2.2.x, we need to pass an existing repository for test.
            # Otherwise the test fail if the folder doesn't exists on the remote server.
            args = []
            args.append("--remote-schema")
            args.append(self._remote_schema())
            args.append("test")
            args.append(self._backup_path(None))
            await self._rdiff_backup(*args)
        elif self.is_local():
            self.find_local_destination()

    def forget(self):
        """
        Disconnect this client from minarca server.
        """
        # Delete configuration file (support deleting readonly file).
        for fn in [
            self.public_key_file,
            self.private_key_file,
            self.known_hosts,
            self.patterns_file,
            self.status_file,
            self.config_file,
        ]:
            if os.path.isfile(fn):
                if not os.access(fn, os.W_OK):
                    os.chmod(fn, stat.S_IWUSR)
                os.remove(fn)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BackupInstance) and self.id == other.id

    def _backup_path(self, path):
        """
        Return the path definin the location of the backup. Either remote or local.
        """
        if path is not None and IS_WINDOWS:
            path = f"/{path[0]}/{path[3:]}"
        if self.is_remote():
            remote_host, unused, unused = self.settings.remotehost.partition(":")
            repositoryname = self.settings.repositoryname
            if path is not None:
                return f"minarca@{remote_host}::{repositoryname}{path}"
            return f"minarca@{remote_host}::."
        elif self.is_local():
            # For local destination, we need to lookup the external drive
            disk = self.find_local_destination()
            if path is not None:
                return os.path.join(disk.mountpoint, disk.relpath) + path
            return os.path.join(disk.mountpoint, disk.relpath)
        else:
            raise NotConfiguredError()

    def find_local_destination(self):
        """
        For local backup, we need to search for our destination since it might change from time to time.
        """
        assert self.settings.localrelpath and self.settings.localuuid
        # Let start by searching our previous location (if any)
        if self.settings.localmountpoint:
            uuid_fn = os.path.join(self.settings.localmountpoint, self.settings.localrelpath, '..', '.minarca-id')
            if file_read(uuid_fn) == self.settings.localuuid:
                path = os.path.join(self.settings.localmountpoint, self.settings.localrelpath)
                return get_location_info(path)

        # Otherwise look on all disk and search our UUID.
        for disk in list_disks():
            uuid_fn = os.path.join(disk.mountpoint, self.settings.localrelpath, '..', '.minarca-id')
            if file_read(uuid_fn) == self.settings.localuuid:
                return disk._replace(relpath=self.settings.localrelpath)
        raise LocalDestinationNotFound()

    def _remote_schema(self):
        """
        Return the remote schema to be pass to rdiff-backup command line argument
        """
        if not self.settings.remotehost:
            raise NotConfiguredError()
        unused, unused, remote_port = self.settings.remotehost.partition(":")

        remote_schema = _escape_path(compat.get_ssh())
        remote_schema += " -oBatchMode=yes -oPreferredAuthentications=publickey"
        if os.environ.get("MINARCA_ACCEPT_HOST_KEY", False) in ["true", "1", "True"]:
            remote_schema += " -oStrictHostKeyChecking=no"
        if remote_port:
            remote_schema += " -p %s" % remote_port
        # SSH options need extract escaping
        remote_schema += " -oUserKnownHostsFile=%s" % _escape_path(self.known_hosts).replace(" ", "\\ ")
        remote_schema += " -oIdentitiesOnly=yes"
        # Identity file must be escape if it contains spaces
        remote_schema += " -i %s" % _escape_path(self.private_key_file)
        # Litera "%s" will get replace by rdiff-backup
        remote_schema += " %s"
        # Add user agent as command line
        remote_schema += " '%s'" % compat.get_user_agent()
        return remote_schema

    async def verify(self):
        args = []
        if self.is_remote():
            args.append("--remote-schema")
            args.append(self._remote_schema())
        args.append("verify")
        args.append(self._backup_path(None))
        await self._rdiff_backup(*args)

    @handle_http_errors
    async def get_disk_usage(self):
        """
        Get disk usage for remote or local backup.
        """
        if self.is_remote():
            # Get quota from server - on authentication failure it's
            # most likely an older minarca server not supporting minarcaid.
            conn = self._remote_conn()
            current_user = await asyncio.get_running_loop().run_in_executor(None, conn.get_current_user_info)
            if 'disk_usage' in current_user and 'disk_quota' in current_user:
                return (current_user['disk_usage'], current_user['disk_quota'])

        elif self.is_local():
            # Get disk usage.
            disk = self.find_local_destination()
            return (disk.used, disk.size)

    def _remote_conn(self):
        """
        Return a new connection to Rdiffweb server.
        """
        with open(self.private_key_file, 'rb') as f:
            private_key_data = f.read()
        conn = Rdiffweb(self.settings.remoteurl)
        conn.auth = private_key_data
        return conn

    @handle_http_errors
    async def save_remote_settings(self, wait=False, timeout=30):
        """
        Push current repository settings to remote server
        Will `wait` for repository to be created for the given `timeout` in seconds.
        Raise a TimeoutError or RemoteRepositoryNotFound.
        """
        assert self.is_remote(), 'only possible to push settings for remote instances'
        assert isinstance(timeout, int), 'expect a timeout as seconds'
        conn = self._remote_conn()
        # Wait for repositories to be created
        repo_name = self.settings.repositoryname
        repo_name_found = False
        start_time = time.time()
        while True:
            current_user = await asyncio.get_running_loop().run_in_executor(None, conn.get_current_user_info)
            repo_name_found = [
                r.get('name')
                for r in current_user.get('repos', [])
                if repo_name == r.get('name') or r.get('name').startswith(repo_name + '/')
            ]
            if repo_name_found:
                break
            elif not wait:
                raise RemoteRepositoryNotFound(repo_name)
            elif time.time() > (start_time + timeout):
                raise TimeoutError()
            await asyncio.sleep(0.2)
        # For each repo, update the settings.
        for repo_name in repo_name_found:
            await asyncio.get_running_loop().run_in_executor(
                None,
                functools.partial(
                    conn.post_repo_settings,
                    repo_name,
                    maxage=self.settings.maxage,
                    keepdays=self.settings.keepdays,
                    ignore_weekday=self.settings.ignore_weekday,
                ),
            )

    @handle_http_errors
    async def load_remote_settings(self):
        """
        Fetch current repository settings from remote server.
        """
        conn = self._remote_conn()
        # Get reference to remote repo
        repo_name = self.settings.repositoryname
        current_user = await asyncio.get_running_loop().run_in_executor(None, conn.get_current_user_info)
        repo_name_found = [
            r.get('name')
            for r in current_user.get('repos', [])
            if repo_name == r.get('name') or r.get('name').startswith(repo_name + '/')
        ]
        if not repo_name_found:
            raise RemoteRepositoryNotFound(repo_name)

        # Get first repo settings.
        data = await asyncio.get_running_loop().run_in_executor(None, conn.get_repo_settings, repo_name_found[0])
        if 'maxage' in data:
            self.settings.maxage = int(data['maxage'])
        if 'keepdays' in data:
            self.settings.keepdays = int(data['keepdays'])
        if 'ignore_weekday' in data and isinstance(data['ignore_weekday'], list):
            self.settings.ignore_weekday = data['ignore_weekday']
        # For interface consistency. We need to get the user's role from remote server.
        if self.is_remote() and 'role' in current_user:
            self.settings.remoterole = int(current_user['role'])

    async def list_increments(self):
        """
        Fetch the increment list from remote server.
        Raise an error if the disk or remote server is not reachable.
        Return dates
        """
        all_increments = []
        # On Windows operating system, the computer may have multiple Root
        # (C:\, D:\, etc). To support this scenario, we need to run
        # rdiff-backup multiple time. Once for each Root.
        for drive, patterns in self.patterns.group_by_roots():
            # Build command line
            args = []
            if self.is_remote():
                # If required add remote-schema to define how to connect to SSH Server
                args.append("--remote-schema")
                args.append(self._remote_schema())
            args.append('--api-version')
            args.append('201')
            args.append('--parsable-output')
            args.append('list')
            args.append('increments')
            args.append(self._backup_path(drive))

            local_tz = get_localzone()

            # Execute command line and pipe result to a file.
            with _Collector('---', '...') as log_file:
                await self._rdiff_backup(*args, log_file=log_file)
                # Then read output as Yaml
                log_file.file.seek(0)
                increments = yaml.safe_load(log_file.file)
                # Extract dateimte as local timezone
                if increments:
                    all_increments.extend(
                        [
                            datetime.datetime.fromtimestamp(inc.get('time'), datetime.timezone.utc).astimezone(local_tz)
                            for inc in increments
                            if 'time' in inc
                        ]
                    )
        return all_increments

    async def list_files(self, increment_datetime):
        """
        Fetch the files list from backup for the given increment date.
        Raise an error if the disk or remote server is not reachable.
        Return files
        """
        assert increment_datetime and isinstance(increment_datetime, datetime.datetime)
        all_files = []
        # On Windows operating system, the computer may have multiple Root
        # (C:\, D:\, etc). To support this scenario, we need to run
        # rdiff-backup multiple time. Once for each Root.
        for drive, patterns in self.patterns.group_by_roots():
            # Build command line
            args = []
            if self.is_remote():
                # If required add remote-schema to define how to connect to SSH Server
                args.append("--remote-schema")
                args.append(self._remote_schema())
            args.append('--api-version')
            args.append('201')
            args.append('--parsable-output')
            args.append('list')
            args.append('files')
            args.append('--at')
            args.append(str(int(increment_datetime.timestamp())))
            args.append(self._backup_path(drive))

            # Execute command line and pipe result to a file.
            with _Collector('.', '*        Cleaning up') as log_file:
                await self._rdiff_backup(*args, log_file=log_file)
                # Then read output as Yaml
                log_file.file.seek(0)
                for line in log_file.file:
                    # TODO use proper icons (try to detect folder vs file)
                    # Remove trailing newline \r\n
                    line = line.rstrip('\r\n')
                    # Ignore "."
                    if line == '.':
                        continue
                    # Prefix with drive
                    path = os.path.join(drive, line)
                    all_files.append(path)

        return all_files
