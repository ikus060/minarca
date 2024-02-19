# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''

import datetime
import logging
import os
import subprocess
import threading
import time

import psutil

from minarca_client.core import compat
from minarca_client.core.compat import IS_WINDOWS, detach_call, file_read, get_minarca_exe, ssh_keygen
from minarca_client.core.config import Datetime, Patterns, Settings, Status
from minarca_client.core.disk import list_disks, sync
from minarca_client.core.exceptions import (
    CaptureException,
    LocalDiskNotFound,
    NoPatternsError,
    NotConfiguredError,
    NotRunningError,
    NotScheduleError,
    RdiffBackupException,
    RdiffBackupExitError,
    RemoteRepositoryNotFound,
    RunningError,
)
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


class _UpdateStatus(threading.Thread):
    """
    Update the status while the backup is running.
    """

    def __init__(self, status, action='backup'):
        assert action in ['backup', 'restore']
        self.status = status
        self.action = action
        super(_UpdateStatus, self).__init__()
        self._stop_event = threading.Event()

    def __enter__(self):
        try:
            from wakepy import set_keepawake

            set_keepawake(keep_screen_awake=False)
        except ImportError:
            # When not supported, an import error is raised
            logger.info("keep awake not supported on this system")
        except Exception:
            logger.warn("failed to set keep awake", exc_info=1)
        logger.info("%s START", self.action)
        self._update_status()
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Wait for thread to stop.
        self.stop()
        if exc_type is not KeyboardInterrupt:
            self.join()
        if exc_type is None:
            logger.info("%s SUCCESS", self.action)
            with self.status as t:
                t.lastresult = 'SUCCESS'
                t.lastsuccess = Datetime()
                t.lastdate = self.status.lastsuccess
                t.details = ''
        else:
            logger.exception("%s FAILED", self.action)
            with self.status as t:
                t.lastresult = 'FAILURE'
                t.lastdate = Datetime()
                t.details = str(exc_val)
        try:
            from wakepy import unset_keepawake

            unset_keepawake()
        except ImportError:
            pass
        except Exception:
            logger.warn("failed to unset keep awake", exc_info=1)

    def run(self):
        while not self.stopped():
            self._update_status()
            time.sleep(Status.RUNNING_DELAY)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def _update_status(self):
        with self.status as t:
            t.pid = os.getpid()
            t.lastresult = 'RUNNING'
            t.lastdate = Datetime()
            t.details = ''
            t.action = self.action


class BackupInstance:
    def __init__(self, id: int | str):
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

    def backup(self, force=False, force_patterns=None):
        """
        Execute the rdiff-backup process.
        Set `force` to True to run backup process event when it's not the time to run.
        Set `force_patterns` with patterns to use instead of default one from settings.
        Set `fork` to True to run the backup processing in a separate process.
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
        status = Status(self.status_file)
        with _UpdateStatus(status=status):
            with open(self.backup_log_file, 'w') as log_file:
                # Pick the right patterns
                patterns = force_patterns if force_patterns is not None else self.patterns
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
                    self._rdiff_backup(*args, drive, dest, log_file=log_file)
                    # For local disk, make sure to "flush" disk cache
                    if self.is_local():
                        logger.info("flush changes to disk")
                        sync(dest)

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
                repo = self.settings.repositoryname + '/' + drive_letter
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
        return self.settings.remotehost and self.settings.repositoryname

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

    def _push_identity(self, rdiffweb, name):
        # Check if ssh keys exists, if not generate new keys.
        if not os.path.exists(self.public_key_file) and not os.path.exists(self.private_key_file):
            logger.debug(_('generating identity'))
            ssh_keygen(self.public_key_file, self.private_key_file)

        # Push SSH Keys to Minarca server
        try:
            with open(self.public_key_file) as f:
                logger.debug(_('exchanging identity with minarca server'))
                rdiffweb.post_ssh_key(name, f.read())
        except Exception:
            # Probably a duplicate SSH Key, let generate new identity
            logger.debug(_('generating new identity'))
            ssh_keygen(self.public_key_file, self.private_key_file)
            # Publish new identify
            with open(self.public_key_file) as f:
                logger.debug(_('exchanging new identity with minarca server'))
                rdiffweb.post_ssh_key(name, f.read())

    def _rdiff_backup(self, *extra_args, log_file=None):
        """
        Make a call to rdiff-backup executable
        """
        # base command line
        args = [get_minarca_exe(), "rdiff-backup", "-v", "5"]
        args.extend(extra_args)

        # Execute the command line.
        capture = CaptureException()
        logger.debug(_('executing command: %s') % _sh_quote(args))
        try:
            p = subprocess.Popen(
                args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                encoding='utf-8',
                errors='replace',
            )
            # Stream the output of rdiff-backup to log file and exception capture.
            for line in p.stdout:
                if log_file:
                    log_file.write(line)
                    log_file.flush()
                capture.parse(line)
            # Check return code
            exit_code = p.wait()
        except Exception as e:
            if capture.exception:
                raise capture.exception
            logger.debug('backup process terminated with an exception', exc_info=1)
            raise RdiffBackupException(str(e))
        else:
            if capture.exception:
                raise capture.exception
            if exit_code not in [0, 2, 8]:
                raise RdiffBackupExitError(exit_code)

    def restore(self, restore_time=None, patterns=None):
        """
        Used to run a complete restore of data backup for the given date or latest date is not defined.
        """
        if self.is_running():
            raise RunningError()
        status = Status(self.status_file)
        with _UpdateStatus(status=status, action='restore'):
            with open(self.backup_log_file, 'w') as log_file:
                # Loop on each pattern to be restored and execute rdiff-backup.
                patterns = patterns or self.patterns
                for p in patterns:
                    if p.include and not p.is_wildcard():
                        self._rdiff_backup(
                            "--force",
                            "--at",
                            restore_time or "now",
                            self._backup_path(p.pattern),
                            p.pattern,
                            log_file=log_file,
                        )

    def start(self, action="backup", force=False, patterns=None):
        """
        Trigger execution of minarca in detach mode.
        """
        assert action in ['backup', 'restore', 'verify']
        # Fork process
        args = [get_minarca_exe(), action]
        if force:
            args += ['--force']
        args += ['--limit', str(self.id)]
        if patterns:
            assert action == 'restore'
            args += [p.pattern for p in patterns]
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
            logger.warn('error trying to stop minarca', exc_info=1)
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

    def test_connection(self):
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
            self._rdiff_backup(*args)
        elif self.is_local():
            self.find_local_disk()

    def forget(self):
        """
        Disconnect this client from minarca server.
        """
        # Delete configuration file.
        for fn in [
            self.public_key_file,
            self.private_key_file,
            self.known_hosts,
            self.patterns_file,
            self.status_file,
            self.config_file,
        ]:
            if os.path.isfile(fn):
                os.remove(fn)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, BackupInstance) and self.id == other.id

    def _backup_path(self, path):
        """
        Return the path definin the location of the backup. Either remote or local.
        """
        if path is not None and IS_WINDOWS:
            path = f"{path[0]}/{path[3:]}"
        if self.is_remote():
            remote_host, unused, unused = self.settings.remotehost.partition(":")
            repositoryname = self.settings.repositoryname
            if path is not None:
                return f"minarca@{remote_host}::{repositoryname}{path}"
            return f"minarca@{remote_host}::."
        elif self.is_local():
            # For local destination, we need to lookup the external drive
            disk = self.find_local_disk()
            if path is not None:
                return os.path.join(disk.mountpoint, self.settings.localrelpath) + path
            return os.path.join(disk.mountpoint, self.settings.localrelpath)
        else:
            raise NotConfiguredError()

    def find_local_disk(self):
        assert self.settings.localrelpath and self.settings.localuuid
        for d in list_disks():
            uuid_fn = os.path.join(d.mountpoint, self.settings.localrelpath, '..', '.minarca-id')
            if file_read(uuid_fn) == self.settings.localuuid:
                return d
        raise LocalDiskNotFound()

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

    def verify(self):
        args = []
        if self.is_remote():
            args.append("--remote-schema")
            args.append(self._remote_schema())
        args.append("verify")
        args.append(self._backup_path(None))
        self._rdiff_backup(*args)

    def get_disk_usage(self):
        """
        Get disk usage for remote or local backup.
        """
        if self.is_remote():
            # Get quota from server - on authentication failure it's
            # most likely an older minarca server not supporting minarcaid.
            conn = self._remote_conn()
            current_user = conn.get_current_user_info()
            if 'disk_usage' in current_user and 'disk_quota' in current_user:
                return (current_user['disk_usage'], current_user['disk_quota'])

        elif self.is_local():
            # Get disk usage.
            disk = self.find_local_disk()
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

    def save_remote_settings(self, wait=False, timeout=30):
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
            current_user = conn.get_current_user_info()
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
        # For each repo, update the settings.
        for repo_name in repo_name_found:
            conn.post_repo_settings(
                repo_name,
                maxage=self.settings.maxage,
                keepdays=self.settings.keepdays,
                ignore_weekday=self.settings.ignore_weekday,
            )
