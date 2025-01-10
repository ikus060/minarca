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
import time
from pathlib import Path

import psutil
from requests.exceptions import ConnectionError, HTTPError, InvalidSchema, MissingSchema
from tzlocal import get_localzone

from minarca_client.core import compat
from minarca_client.core.compat import IS_WINDOWS, detach_call, file_read, flush, get_minarca_exe
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
from minarca_client.core.pattern import Patterns
from minarca_client.core.rdiffweb import Rdiffweb
from minarca_client.core.settings import Datetime, Settings
from minarca_client.core.status import Status, UpdateStatus, UpdateStatusNotification

logger = logging.getLogger(__name__)


def _sh_quote(args):
    """
    Used for logging only. Escape command line.
    """
    value = ''
    for a in args:
        a = str(a)
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
    if ' ' not in str(path):
        return str(path)
    if IS_WINDOWS:
        import win32api

        return win32api.GetShortPathName(str(path))
    return "'%s'" % path


async def _read_stream(stream, capture, callback):
    """
    Asynchronously read stream and send result to capture exception and callback function.
    """
    while True:
        try:
            line = await stream.readline()
        except ValueError:
            # Raised by readline when the line doesn't fit in the buffer.
            # Common case when running rdiff-backup with "-v 9"
            callback('OUTPUT LOST')
        if line:
            capture.parse(line)
            callback(line)
        else:
            # EOF
            break


def reduce_path(paths):
    """
    Remove already included files from the list.
    """
    reduced_paths = []

    for path in paths:
        # Check if the path is already encompassed by any in reduced_paths
        if not any(os.path.commonpath([path, included]) == included for included in reduced_paths):
            reduced_paths.append(path)

    return reduced_paths


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


@contextlib.contextmanager
def safe_keepawake():
    """Safe implementation of keepawake"""
    try:
        from wakepy import set_keepawake

        set_keepawake(keep_screen_awake=False)
    except ImportError:
        # When not supported, an import error is raised
        logger.warning("keep awake not supported on this system")
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


class BackupInstance:
    def __init__(self, id):
        """
        Create a new minarca backup instance.
        """
        assert (isinstance(id, int) and id >= 0) or isinstance(id, str)
        self.id = id
        self.log_id = f'instance {self.id}' if str(self.id) else 'instance default'
        # Get file locations.
        self.public_key_file = compat.get_config_home() / f"id_rsa{id}.pub"
        self.private_key_file = compat.get_config_home() / f"id_rsa{id}"
        self.known_hosts = compat.get_config_home() / f"known_hosts{id}"
        self.config_file = compat.get_config_home() / f"minarca{id}.properties"
        self.patterns_file = compat.get_config_home() / f"patterns{id}"
        self.status_file = compat.get_data_home() / f"status{id}.properties"
        self.backup_log_file = compat.get_data_home() / f"backup{id}.log"
        self.restore_log_file = compat.get_data_home() / f"restore{id}.log"
        # Create wrapper around config files.
        self.patterns = Patterns(self.patterns_file)
        self.status = Status(self.status_file)
        self.settings = Settings(self.config_file)

    async def backup(self, force=False):
        """
        Execute the rdiff-backup process.
        Set `force` to True to run backup process even when it's not the time to run.
        """
        logger.debug(f"{self.log_id}: starting backup with force: {force}")
        # Check if it's time to run a backup
        if self.is_running():
            raise RunningError()
        if not force and not self.is_backup_time():
            raise NotScheduleError()

        # Clear pause if backup started with force
        if self.settings.pause_until is not None:
            logger.debug(f"{self.log_id}: clearing pause setting as backup started with force")
            self.settings.pause_until = None
            self.settings.save()

        with safe_keepawake():
            with UpdateStatusNotification(instance=self):
                async with UpdateStatus(instance=self):
                    with open(self.backup_log_file, 'wb') as log_file:
                        now = Datetime()
                        log_file.write(b'starting backup at %s\n' % now.strftime().encode())
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
                            args.extend(["--exclude", f"{drive}**"])
                            # Call rdiff-backup
                            dest = self._backup_path(drive)
                            await self._rdiff_backup(*args, drive, dest, callback=log_file.write)
                            # For local disk, make sure to "flush" disk cache
                            if self.is_local():
                                logger.debug(f"{self.log_id}: flushing changes to disk")
                                flush(dest)

                            # # For local disk, we need to manage the retention period too.
                            if self.is_local() and self.settings.keepdays and self.settings.keepdays > 0:
                                await self._rdiff_backup(
                                    '--force',
                                    'remove',
                                    'increments',
                                    '--older-than',
                                    f"{self.settings.keepdays}D",
                                    dest,
                                    callback=log_file.write,
                                )
        logger.debug(f"{self.log_id}: backup process completed successfully")

    def get_repo_url(self, page="browse"):
        """
        Return a URL to browse data. Either https:// or file://
        """
        logger.debug(f"{self.log_id}: generating repo URL for page: {page}")
        if self.is_remote():
            assert page in ['browse', 'settings']
            if IS_WINDOWS:
                # On Windows, we append a drive letter.
                drive_letter, _ = next(self.patterns.group_by_roots(), (None, []))
                if not drive_letter:
                    return self.settings.remoteurl
                repo = f"{self.settings.repositoryname}/{drive_letter[0]}"
            else:
                repo = self.settings.repositoryname
            return f"{self.settings.remoteurl}/{page}/{self.settings.username}/{repo}"
        else:
            assert page in ['browse']
            return f"file://{self._backup_path(None)}"

    def get_help_url(self):
        """
        Return a URL to help.
        """
        if self.settings.remoteurl:
            return f"{self.settings.remoteurl}/help"

    def is_backup_time(self):
        """
        Check if it's time to backup.
        """
        # Check if manual.
        if self.settings.schedule <= 0:
            logger.debug(f"{self.log_id}: backup schedule is manual")
            return False
        # Check if paused.
        logger.debug(f"{self.log_id}: checking if it's backup time")
        pause_until = self.settings.pause_until
        if pause_until and Datetime() < pause_until:
            logger.debug(f"{self.log_id}: backup paused until {pause_until.strftime()}")
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
        return self.status.current_status == 'RUNNING'

    def is_local(self):
        return bool(self.settings.localuuid and self.settings.localrelpath)

    def is_remote(self):
        return bool(self.settings.remotehost and self.settings.repositoryname)

    def pause(self, delay):
        """
        Used to prevent execution of backup for a given period of time in hours.
        """
        assert isinstance(delay, int)
        # Store absolute time for calculation.
        if delay > 0:
            self.settings.pause_until = Datetime() + datetime.timedelta(hours=delay)
        else:
            self.settings.pause_until = None
        self.settings.save()
        logger.debug(f"{self.log_id}: backup paused for {delay} hours")

    async def _push_identity(self, conn, name):
        if not self.public_key_file.exists() and not self.private_key_file.exists():
            logger.debug(f"{self.log_id}: generating new SSH identity")
            ssh_keygen(self.public_key_file, self.private_key_file)

        try:
            with open(self.public_key_file, encoding='latin-1') as f:
                logger.debug(f"{self.log_id}: exchanging SSH identity with server")
                await asyncio.get_running_loop().run_in_executor(None, conn.post_ssh_key, name, f.read())
        except Exception:
            logger.debug(f"{self.log_id}: generating new SSH identity after failure")
            ssh_keygen(self.public_key_file, self.private_key_file)
            with open(self.public_key_file, encoding='latin-1') as f:
                logger.debug(f"{self.log_id}: exchanging new SSH identity with server")
                await asyncio.get_running_loop().run_in_executor(None, conn.post_ssh_key, name, f.read())

    async def _rdiff_backup(self, *extra_args, callback=None):
        """
        Make a call to rdiff-backup executable.
        """
        args = ["rdiff-backup", "-v", "5"]
        args.extend(extra_args)

        capture = CaptureException()
        if callback is None:

            def callback(line):
                line = line.decode('utf-8', errors='replace').rstrip('\r\n')
                logger.debug(f"{self.log_id}: {line}")

        logger.debug(f"{self.log_id}: executing command: {_sh_quote(args)}")
        try:
            # Enforce UTF-8 to be used by rdiff-backup stdout.
            env = os.environ.copy()
            env['PYTHONUTF8'] = '1'
            # Do not create a window
            creationflags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
            process = await asyncio.create_subprocess_exec(
                get_minarca_exe(),
                *args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                creationflags=creationflags,
            )
            # Stream stdout and stderr
            await asyncio.tasks.gather(
                _read_stream(process.stdout, capture, callback),
                _read_stream(process.stderr, capture, callback),
            )
            # Check return code
            exit_code = await process.wait()
        except Exception as e:
            if capture.exception:
                raise capture.exception
            raise RdiffBackupException(str(e))
        else:
            if capture.exception:
                raise capture.exception
            if exit_code not in [0, 2, 8]:
                raise RdiffBackupExitError(exit_code)

    async def restore(self, restore_time=None, paths=[], destination=None):
        """
        Used to run a complete restore of data backup for the given date or latest date if not defined.
        """
        assert restore_time is None or isinstance(restore_time, str)
        assert isinstance(paths, list) and all(isinstance(p, (str, Path)) for p in paths)
        assert destination is None or isinstance(destination, (str, Path))
        if self.is_running():
            raise RunningError()
        with safe_keepawake():
            async with UpdateStatus(instance=self, action='restore'):
                with open(self.restore_log_file, 'wb') as log_file:
                    now = Datetime()
                    log_file.write(b'starting restore at %s\n' % now.strftime().encode())
                    # Loop on each pattern to be restored and execute rdiff-backup.
                    for path in reduce_path(paths):
                        if destination:
                            # Restore into different location
                            final_destination = os.path.join(str(destination), os.path.basename(str(path)))
                        else:
                            # Restore in place
                            final_destination = path
                        # Force is required to replace folder
                        args = ["--force"]
                        # If required add remote-schema to define how to connect to SSH Server
                        if self.is_remote():
                            args.append("--remote-schema")
                            args.append(self._remote_schema())
                        args += [
                            "restore",
                            "--at",
                            restore_time or "now",
                            self._backup_path(str(path)),
                            str(final_destination),
                        ]
                        # FIXME For full restore we should add exclude pattern, but rdiff-backup raise an error.
                        await self._rdiff_backup(
                            *args,
                            callback=log_file.write,
                        )

    def start_backup(self, force=False):
        """
        Trigger execution of minarca in detach mode.
        """
        args = [get_minarca_exe(), 'backup']
        if force:
            args += ['--force']
        args += ['--instance', str(self.id)]
        child = detach_call(args)
        logger.debug(f"{self.log_id}: subprocess {child.pid} started for backup: {_sh_quote(args)}")

    def start_restore(self, restore_time=None, paths=[], destination=None):
        assert restore_time is None or isinstance(restore_time, int)
        assert isinstance(paths, (list, str))
        if isinstance(paths, str):
            paths = [paths]
        assert paths
        assert destination is None or isinstance(destination, str)

        args = [get_minarca_exe(), 'restore']
        args += ['--force']
        args += ['--instance', str(self.id)]
        if restore_time:
            args += ['--restore-time', str(restore_time)]
        if destination:
            args += ['--destination', str(destination)]
        args += paths
        child = detach_call(args)
        logger.debug(f"{self.log_id}: subprocess {child.pid} started for restore: {args}")

    def stop(self):
        """
        Stop the running backup process.
        """
        # Check status for running backup.
        if not self.is_running():
            raise NotRunningError()

        # Get pid and check if process is running.
        pid = self.status.pid
        logger.debug(f"{self.log_id}: stopping backup process with PID: {pid}")
        p = psutil.Process(pid)
        if not p.is_running():
            raise NotRunningError()

        # Send appropriate signal
        logger.debug(f"{self.log_id}: terminating process {pid}")
        try:
            # To terminate the backup, the best is to kill the SSH connection.
            for child in p.children(recursive=True):
                if 'ssh.exe' in child.name() or 'ssh' in child.name():
                    child.terminate()
            p.terminate()
        except SystemError:
            logger.error(f"{self.log_id}: error trying to stop process", exc_info=True)

        # Wait until process gets killed
        count = 1
        while p.is_running() and count < 10:
            time.sleep(0.1)
            count += 1

        # Replace status by INTERRUPT
        logger.debug(f"{self.log_id}: process interrupted successfully")
        with self.status as t:
            t.lastresult = 'INTERRUPT'
            t.lastdate = Datetime()
            t.details = ''

    async def test_connection(self):
        """
        Check connectivity to the remote server or local disk using rdiff-backup.
        """
        logger.debug(f"{self.log_id}: testing connection")
        if self.is_remote():
            # Since v2.2.x, we need to pass an existing repository for test.
            # Otherwise the test fail if the folder doesn't exist on the remote server.
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
        Disconnect this client from server.
        """
        logger.debug(f"{self.log_id}: forgetting this instance from server")
        # Delete configuration file (support deleting readonly file).
        for fn in [
            self.public_key_file,
            self.private_key_file,
            self.known_hosts,
            self.patterns_file,
            self.status_file,
            self.config_file,
        ]:
            if fn.is_file():
                fn.chmod(stat.S_IWUSR)
                fn.unlink()
                logger.debug(f"{self.log_id}: deleted file: {fn}")

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BackupInstance) and self.id == other.id

    def _backup_path(self, path):
        """
        Return the path defining the location of the backup. Either remote or local.
        """
        assert path is None or isinstance(path, str)
        logger.debug(f"{self.log_id}: constructing backup path for {path}")
        if path is not None and IS_WINDOWS:
            path = f"/{path[0]}/{path[3:]}"
        if self.is_remote():
            remote_host, unused, unused = self.settings.remotehost.partition(":")
            repositoryname = self.settings.repositoryname
            if path is not None:
                backup_path = f"minarca@{remote_host}::{repositoryname}{path}"
                logger.debug(f"{self.log_id}: remote backup path: {backup_path}")
                return backup_path
            backup_path = f"minarca@{remote_host}::."
            logger.debug(f"{self.log_id}: remote backup path: {backup_path}")
            return backup_path
        elif self.is_local():
            # For local destination, we need to lookup the external drive
            disk = self.find_local_destination()
            if path is not None:
                backup_path = disk / path.lstrip('/').lstrip('\\')
                logger.debug(f"{self.log_id}: local backup path: {backup_path}")
                return backup_path
            logger.debug(f"{self.log_id}: local backup path: {disk}")
            return disk
        raise NotConfiguredError()

    def find_local_destination(self):
        """
        For local backup, we need to search for our destination since it might change from time to time.
        """
        assert self.settings.localrelpath and self.settings.localuuid, 'only supported for local backup'
        logger.debug(f"{self.log_id}: finding local destination")

        # Let start by searching our previous location (if any)
        if self.settings.localmountpoint:
            uuid_fn = Path(self.settings.localmountpoint) / self.settings.localrelpath / '..' / '.minarca-id'
            if file_read(uuid_fn) == self.settings.localuuid:
                destination = Path(self.settings.localmountpoint) / self.settings.localrelpath
                logger.debug(f"{self.log_id}: found local destination: {destination}")
                return destination

        # Otherwise look on all disks and search our UUID.
        for disk in list_disks():
            uuid_fn = disk / self.settings.localrelpath / '..' / '.minarca-id'
            if file_read(uuid_fn) == self.settings.localuuid:
                destination = Path(disk) / self.settings.localrelpath
                logger.debug(f"{self.log_id}: found local destination: {destination}")
                return destination

        raise LocalDestinationNotFound()

    def _remote_schema(self):
        """
        Return the remote schema to be passed to rdiff-backup command line argument.
        """
        if not self.settings.remotehost:
            raise NotConfiguredError()

        unused, unused, remote_port = self.settings.remotehost.partition(":")
        remote_schema = _escape_path(compat.get_ssh())
        # Enforce a null config file to avoid reading system wide configuration
        if not IS_WINDOWS:
            remote_schema += " -F /dev/null"
        remote_schema += " -oBatchMode=yes -oPreferredAuthentications=publickey"
        if os.environ.get("MINARCA_ACCEPT_HOST_KEY", False) in ["true", "1", "True"]:
            remote_schema += " -oStrictHostKeyChecking=no"
        if remote_port:
            remote_schema += " -p %s" % remote_port
        # SSH options need extra escaping
        remote_schema += " -oUserKnownHostsFile=%s" % _escape_path(self.known_hosts).replace(" ", "\\ ")
        remote_schema += " -oIdentitiesOnly=yes"
        # Identity file must be escaped if it contains spaces
        remote_schema += " -i %s" % _escape_path(self.private_key_file)
        # Literal "%s" will get replaced by rdiff-backup
        remote_schema += " %s"
        # Add user agent as command line
        remote_schema += " '%s'" % compat.get_user_agent()
        logger.debug(f"{self.log_id}: remote schema: {remote_schema}")
        return remote_schema

    async def verify(self):
        args = []
        if self.is_remote():
            args.append("--remote-schema")
            args.append(self._remote_schema())

        args.append("verify")
        args.append(self._backup_path(None))
        logger.debug(f"{self.log_id}: verify instance with : {args}")
        await self._rdiff_backup(*args)

    @handle_http_errors
    async def get_disk_usage(self):
        """
        Get disk usage for remote or local backup.
        """
        logger.debug(f"{self.log_id}: getting disk usage")
        if self.is_remote():
            # Get quota from server - on authentication failure it's
            # most likely an older minarca server not supporting minarcaid.
            conn = self._remote_conn()
            current_user = await asyncio.get_running_loop().run_in_executor(None, conn.get_current_user_info)
            if 'disk_usage' in current_user and 'disk_quota' in current_user:
                disk_usage = (current_user['disk_usage'], current_user['disk_quota'])
                logger.debug(f"{self.log_id}: remote disk usage: {disk_usage}")
                return disk_usage
        elif self.is_local():
            # Get disk usage.
            disk = self.find_local_destination()
            detail = get_location_info(disk)
            disk_usage = (detail.used, detail.size)
            logger.debug(f"{self.log_id}: local disk usage: {disk_usage}")
            return disk_usage

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
        logger.debug(f"{self.log_id}: saving remote settings with wait={wait} and timeout={timeout}")
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
            logger.debug(f"{self.log_id}: updated remote repository settings for: {repo_name}")

    @handle_http_errors
    async def load_remote_settings(self):
        """
        Fetch current repository settings from remote server.
        """
        logger.debug(f"{self.log_id}: loading remote settings")
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
        logger.debug(f"{self.log_id}: loaded remote settings: {self.settings}")

    async def list_increments(self):
        """
        Fetch the increment list from remote server.
        Raise an error if the disk or remote server is not reachable.
        Return dates
        """
        logger.debug(f"{self.log_id}: listing increments")

        local_tz = get_localzone()
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

            def collect_increments(line):
                """
                Collect the increment time from rdiff-backup output.
                """
                # The output is in yaml format, but let capture only the `time:` values.
                if not line.startswith(b'  time: '):
                    return
                try:
                    epoch_value = int(line[8:])
                except ValueError:
                    logger.warning(f"{self.log_id}: invalid increment time: {line[8:]}")
                date_value = datetime.datetime.fromtimestamp(epoch_value, datetime.timezone.utc).astimezone(local_tz)
                all_increments.append(date_value)

            # Call rdiff-backup
            await self._rdiff_backup(*args, callback=collect_increments)

        logger.debug(f"{self.log_id}: found {len(all_increments)} increments")
        return all_increments

    async def list_files(self, increment_datetime):
        """
        Fetch the files list from backup for the given increment date.
        Raise an error if the disk or remote server is not reachable.
        Return files
        """
        assert increment_datetime and isinstance(increment_datetime, datetime.datetime)
        logger.debug(f"{self.log_id}: listing files for increment date: {increment_datetime}")

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

            collect = False

            def collect_files(line, drive=drive):
                """
                Collect the file names. Everything between `.` and `*        Cleaning up`
                """
                nonlocal collect
                if b'Cleaning up' in line:
                    collect = False
                elif line == b'.\n' or line == b'.\r\n':
                    collect = True
                elif collect:
                    # TODO Fix handling of invalid encoding. rdiff-backup replace everything by U+FFFD
                    # Ref.: https://github.com/rdiff-backup/rdiff-backup/issues/1050
                    line = line.decode('utf-8', errors='replace').rstrip('\r\n')
                    path = os.path.join(drive, line)
                    all_files.append(path)

            # Execute command line and collect filenames
            await self._rdiff_backup(*args, callback=collect_files)

        logger.debug(f"{self.log_id}: found {len(all_files)} files")
        return all_files
