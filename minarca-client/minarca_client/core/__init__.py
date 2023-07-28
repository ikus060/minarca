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
import re
import subprocess
import threading
import time
from datetime import timedelta

import psutil
import requests
from psutil import NoSuchProcess
from requests.compat import urljoin
from requests.exceptions import ConnectionError, HTTPError, InvalidSchema, MissingSchema

from minarca_client.core import compat
from minarca_client.core.compat import IS_WINDOWS, Scheduler, get_minarca_exe, ssh_keygen
from minarca_client.core.config import Datetime, Patterns, Settings, Status
from minarca_client.core.exceptions import (
    CaptureException,
    HttpAuthenticationError,
    HttpConnectionError,
    HttpInvalidUrlError,
    HttpServerError,
    NoPatternsError,
    NotConfiguredError,
    NotRunningError,
    NotScheduleError,
    RdiffBackupException,
    RdiffBackupExitError,
    RepositoryNameExistsError,
    RunningError,
)
from minarca_client.locale import _

_REPOSITORY_NAME_PATTERN = "^[a-zA-Z0-9][a-zA-Z0-9\\-\\.]*$"

_RUNNING_DELAY = 5  # 5 seconds

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
            self.status['lastresult'] = 'SUCCESS'
            self.status['lastsuccess'] = Datetime()
            self.status['lastdate'] = self.status['lastsuccess']
            self.status['details'] = ''
            self.status.save()
        else:
            logger.exception("%s FAILED", self.action)
            self.status['lastresult'] = 'FAILURE'
            self.status['lastdate'] = Datetime()
            self.status['details'] = str(exc_val)
            self.status.save()
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
            time.sleep(_RUNNING_DELAY)

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    def _update_status(self):
        self.status['pid'] = os.getpid()
        self.status['lastresult'] = 'RUNNING'
        self.status['lastdate'] = Datetime()
        self.status['details'] = ''
        self.status['action'] = self.action
        self.status.save()


class Backup:
    def __init__(self):
        """
        Create a new minarca backup backup.
        """
        # Get file location.
        self.public_key_file = os.path.join(compat.get_config_home(), "id_rsa.pub")
        self.private_key_file = os.path.join(compat.get_config_home(), "id_rsa")
        self.known_hosts = os.path.join(compat.get_config_home(), "known_hosts")
        self.config_file = os.path.join(compat.get_config_home(), "minarca.properties")
        self.patterns_file = os.path.join(compat.get_config_home(), "patterns")
        self.status_file = os.path.join(compat.get_data_home(), 'status.properties')
        self.scheduler = Scheduler()

    def start(self, action='backup', force=False, patterns=None):
        """
        Trigger execution of minarca in detach mode.
        """
        assert action in ['backup', 'restore']
        # Fork process
        args = [get_minarca_exe(), action]
        if force:
            args += ['--force']
        if patterns:
            assert action == 'restore'
            args += [p.pattern for p in patterns]
        creationflags = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
            if IS_WINDOWS
            else 0
        )
        child = subprocess.Popen(
            args,
            stdin=None,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=creationflags,
        )
        logger.info('subprocess %s started' % child.pid)

    def backup(self, force=False, force_patterns=None):
        """
        Execute the rdiff-backup process.
        Set `force` to True to run backup process event when it's not the time to run.
        Set `force_patterns` with patterns to use instead of default one from settings.
        Set `fork` to True to run the backup processing in a separate process.
        """
        # Check if it'S time to run a backup
        if self.is_running():
            raise RunningError()
        if not force and not self.is_backup_time():
            raise NotScheduleError()

        # Clear pause if backup started with force
        if self.get_settings('pause_until'):
            self.set_settings('pause_until', None)

        # Start a thread to update backup status.
        status = Status(self.status_file)
        with _UpdateStatus(status=status):
            # Pick the right patterns
            patterns = force_patterns if force_patterns is not None else Patterns(self.patterns_file)
            if not patterns:
                raise NoPatternsError()

            # On Windows operating system, the computer may have multiple Root
            # (C:\, D:\, etc). To support this scenario, we need to run
            # rdiff-backup multiple time on the same computer. Once for each Root
            # to be backup (if required).
            for drive, patterns in patterns.group_by_roots():
                if IS_WINDOWS:
                    args = [
                        '--no-hard-links',
                        '--exclude-symbolic-links',
                        '--create-full-path',
                        '--no-compression',
                    ]
                else:
                    args = [
                        '--exclude-sockets',
                        '--no-compression',
                    ]
                for p in patterns:
                    args.append('--include' if p.include else '--exclude')
                    args.append(p.pattern)
                args.extend(['--exclude', '%s**' % drive])
                self._rdiff_backup(extra_args=args, path=drive)

    def get_patterns(self):
        """
        Return list of include/exclude patterns
        """
        return Patterns(self.patterns_file)

    def get_repo_url(self, page='browse'):
        """
        Return a URL to browse data.
        """
        assert page in ['browse', 'settings']
        settings = self.get_settings()
        if IS_WINDOWS:
            # On Windows, we happen a drive letter.
            roots = list(self.get_patterns().group_by_roots())
            if not roots:
                return settings['remoteurl']
            drive_letter = roots[0][0][0]
            repo = settings['repositoryname'] + '/' + drive_letter
        else:
            repo = settings['repositoryname']
        return "%s/%s/%s/%s" % (settings['remoteurl'], page, settings['username'], repo)

    def get_help_url(self):
        """
        Return a URL to help.
        """
        settings = self.get_settings()
        return "%s/help" % (settings['remoteurl'],)

    def get_settings(self, key=None):
        """
        Return configuration.
        """
        config = Settings(self.config_file)
        if key:
            return config[key]
        return config

    def set_settings(self, key, value):
        """
        Return configuration.
        """
        config = Settings(self.config_file)
        config[key] = value
        config.save()

    def get_status(self, key=None):
        """
        Return a backup status. Read data from the status file and make
        interpretation of it.
        """
        # TODO We should cache the status file and only return a new value if
        # the modification time changed.
        now = Datetime()
        status = Status(self.status_file)
        # After reading the status file, let determine the real status.
        if status['lastresult'] == 'RUNNING':
            # Get pid and checkif process is running.
            try:
                is_running = status['pid'] and psutil.Process(int(status['pid'])).is_running()
            except (ValueError, NoSuchProcess):
                is_running = False
            if not is_running:
                status['lastresult'] = 'INTERRUPT'
            elif status['lastdate'] and now - status['lastdate'] > timedelta(seconds=_RUNNING_DELAY * 2):
                status['lastresult'] = 'STALE'
        if key:
            return status[key]
        return status

    def is_linked(self):
        """
        Return True if the backup is configured with a minarca server.
        """
        config = self.get_settings()
        return config['configured']

    def is_backup_time(self):
        """
        Check if it's time to backup.
        """
        # Check if paused.
        pause_until = self.get_settings('pause_until')
        if pause_until and Datetime() < pause_until:
            return False
        # Check if backup ever ran.
        lastsuccess = self.get_status('lastsuccess')
        if lastsuccess is None:
            return True
        # Check if interval passed
        interval = datetime.timedelta(hours=self.get_settings('schedule') * 98.0 / 100)
        time_since_last_backup = Datetime() - lastsuccess
        return interval < time_since_last_backup

    def is_running(self):
        """
        Return true if a backup is running.
        """
        # Check status for running backup.
        return self.get_status('lastresult') == 'RUNNING'

    def link(self, remoteurl, username, password, repository_name, force=False):
        """
        Link the computer with minarca server.
        Set `force` to True to link event if the repository name already exists.
        """
        # Validate the repository name
        if not repository_name or not re.match(_REPOSITORY_NAME_PATTERN, repository_name):
            raise ValueError("repository must only contains letters, numbers, dash (-) and dot (.)")

        try:
            # Check if the repository already exists for the guven user.
            rdiffweb = Rdiffweb(remoteurl, username, password)
            current_user = rdiffweb.get_current_user_info()
            exists = any(
                repository_name == r.get('name') or r.get('name').startswith(repository_name + '/')
                for r in current_user.get('repos', [])
            )
            if not force and exists:
                raise RepositoryNameExistsError(repository_name)

            # Generate SSH Keys
            self._push_identity(rdiffweb, repository_name)

            # Store minarca identity
            minarca_info = rdiffweb.get_minarca_info()
            with open(self.known_hosts, 'w') as f:
                f.write(minarca_info['identity'])

            # Create default config
            config = self.get_settings()
            config['username'] = username
            config['repositoryname'] = repository_name
            config['remotehost'] = minarca_info['remotehost']
            config['remoteurl'] = remoteurl
            config['schedule'] = Settings.DAILY
            config.save()

            # Only test the connection
            self.test_server()

            # Define default patterns if none are define.
            patterns = Patterns(self.patterns_file)
            if len(list(patterns.group_by_roots())) == 0:
                patterns.defaults()
                patterns.save()

            # Define default status
            status = Status(self.status_file)
            status.clear()
            status.save()

            # etc.
            config['configured'] = True
            config.save()
        except ConnectionError:
            # Raised with invalid url or port
            raise HttpConnectionError(remoteurl)
        except (MissingSchema, InvalidSchema):
            raise HttpInvalidUrlError(remoteurl)
        except HTTPError as e:
            # Raise for invalid status code.
            if e.response.status_code in [401, 403]:
                raise HttpAuthenticationError(e)
            raise HttpServerError(e)

    def pause(self, delay):
        """
        Used to prevent execution of backup for a given periode of time in hours.
        """
        assert isinstance(delay, int)
        # Store absolute time for calculation.
        if delay > 0:
            self.set_settings('pause_until', Datetime() + datetime.timedelta(hours=delay))
        else:
            self.set_settings('pause_until', None)

    def _push_identity(self, rdiffweb, name):
        # Check if ssh keys exists, if not generate new keys.
        if not os.path.exists(self.public_key_file) and not os.path.exists(self.private_key_file):
            logger.debug(_('generating identity'))
            ssh_keygen(self.public_key_file, self.private_key_file)

        # Push SSH Keys to Minarca server
        try:
            with open(self.public_key_file) as f:
                logger.debug(_('exchanging identity with minarca server'))
                rdiffweb.add_ssh_key(name, f.read())
        except Exception:
            # Probably a duplicate SSH Key, let generate new identity
            logger.debug(_('generating new identity'))
            ssh_keygen(self.public_key_file, self.private_key_file)
            # Publish new identify
            with open(self.public_key_file) as f:
                logger.debug(_('exchanging new identity with minarca server'))
                rdiffweb.add_ssh_key(name, f.read())

    def _rdiff_backup(self, action='backup', extra_args=[], path=None):
        """
        Make a call to rdiff-backup executable
        """
        assert action in ['backup', 'restore', 'test']
        # Read config file for remote host
        config = self.get_settings()
        if not config['remotehost']:
            raise NotConfiguredError()
        if not config['repositoryname']:
            raise NotConfiguredError()
        remote_host, unused, remote_port = config['remotehost'].partition(':')
        repositoryname = config['repositoryname']

        # base command line
        args = [get_minarca_exe(), 'rdiff-backup', '-v', '5', '--remote-schema']
        remote_schema = _escape_path(compat.get_ssh())
        remote_schema += " -oBatchMode=yes -oPreferredAuthentications=publickey"
        if os.environ.get('MINARCA_ACCEPT_HOST_KEY', False) in ['true', '1', 'True']:
            remote_schema += ' -oStrictHostKeyChecking=no'
        if remote_port:
            remote_schema += ' -p %s' % remote_port
        # SSH options need extract escaping
        remote_schema += " -oUserKnownHostsFile=%s" % _escape_path(self.known_hosts).replace(' ', '\\ ')
        remote_schema += " -oIdentitiesOnly=yes"
        # Identity file must be escape if it contains spaces
        remote_schema += " -i %s" % _escape_path(self.private_key_file)
        # Litera "%s" will get replace by rdiff-backup
        remote_schema += " %s"
        # Add user agent as command line
        remote_schema += " '%s'" % compat.get_user_agent()

        args.append(remote_schema)
        # Force operation on restore.
        if action == 'restore':
            args.append('--force')
        args.append(action)
        args.extend(extra_args)

        if path:
            if IS_WINDOWS:
                remote = f"minarca@{remote_host}::{repositoryname}/{path[0]}/{path[3:]}"
            else:
                remote = f"minarca@{remote_host}::{repositoryname}{path}"
        if action == 'backup':
            # For backup local to remote
            args.append(path)
            args.append(remote)
        elif action == 'restore':
            # For restore remote to local
            args.append(remote)
            args.append(path)
        elif action == 'test':
            # For test-server
            args.append(f"minarca@{remote_host}::.")

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
            )
            # stream the output of rdiff-backup.
            for line in p.stdout:
                logger.debug(line.rstrip())
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
            # Loop on each pattern to be restored and execute rdiff-backup.
            patterns = patterns or self.get_patterns()
            for p in patterns:
                if p.include and not p.is_wildcard():
                    self._rdiff_backup(
                        'restore',
                        ['--at', restore_time or "now"],
                        path=p.pattern,
                    )

    def schedule_job(self, run_if_logged_out=None):
        """
        Used to schedule the job in operating system task scheduler. e.g.: crontab.

        On Windows, username and password are required if we want to run the task whenever the user is logged out.
        `run_if_logged_out` should then containe a tuple with username and password.
        """
        # Also schedule task in Operating system scheduler.
        if self.scheduler.exists():
            self.scheduler.delete()
        if IS_WINDOWS:
            self.scheduler.create(run_if_logged_out=run_if_logged_out)
        else:
            self.scheduler.create()

    def set_patterns(self, patterns):
        assert isinstance(patterns, list), 'patterns should be a list'
        p = Patterns(self.patterns_file)
        p.clear()
        # Make sure patterns are uniq
        p.extend(patterns)
        p.save()

    def stop(self):
        """
        Stop the running backup process.
        """
        # Check status for running backup.
        if not self.is_running():
            raise NotRunningError()
        # Get pid and checkif process is running.
        status = self.get_status()
        try:
            pid = int(status['pid'])
        except ValueError:
            raise NotRunningError()
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
        status = self.get_status()
        status['lastresult'] = 'INTERRUPT'
        status['lastdate'] = Datetime()
        status['details'] = ''
        status.save()

    def test_server(self):
        """
        Check connectivity to the remote server using rdiff-backup.
        """
        # Since v2.2.x, we need to pass an existing repository nave for test.
        # Otherwise the test fail if the folder doesn't exists on the remote server.
        self._rdiff_backup('test')

    def unlink(self):
        """
        Disconnect this client from minarca server.
        """
        self.set_settings('configured', False)
        # Remove scheduler
        self.scheduler.delete()


class Rdiffweb:
    def __init__(self, remote_url, username, password):
        # Create HTTP Session using authentication
        assert username
        assert password
        self.username = username
        self.session = requests.Session()
        self.session.allow_redirects = False
        self.session.headers['User-Agent'] = compat.get_user_agent()
        # Check if connection is working and get redirection if needed
        response = self.session.get(urljoin(remote_url + '/', '/api/'), allow_redirects=True)
        # Replace remote_URL by using response URL to support redirection.
        if not response.url.endswith('/api/'):
            raise ConnectionError()
        self.remote_url = response.url[0:-4]
        # Configure authentication
        self.session.auth = (username, password)
        response = self.session.get(urljoin(self.remote_url + '/', "api/"))
        self.raise_for_status(response)

    def add_ssh_key(self, title, public_key):
        response = self.session.post(
            self.remote_url + 'api/currentuser/sshkeys',
            data={'title': title, 'key': public_key},
        )
        self.raise_for_status(response)

    def get_current_user_info(self):
        response = self.session.get(self.remote_url + 'api/currentuser/')
        self.raise_for_status(response)
        return response.json()

    def get_minarca_info(self):
        """
        Return a dict with `version`, `remotehost`, `identity`
        """
        response = self.session.get(self.remote_url + 'api/minarca/')
        self.raise_for_status(response)
        return response.json()

    def raise_for_status(self, response):
        """Raises :class:`HTTPError`, if one occurred."""

        http_error_msg = ""
        if isinstance(response.reason, bytes):
            # We attempt to decode utf-8 first because some servers
            # choose to localize their reason strings. If the string
            # isn't utf-8, we fall back to iso-8859-1 for all other
            # encodings. (See PR #3538)
            try:
                reason = response.reason.decode("utf-8")
            except UnicodeDecodeError:
                reason = response.reason.decode("iso-8859-1")
        else:
            reason = response.reason

        if 100 <= response.status_code < 200:
            http_error_msg = f"{response.status_code} Informational response: {reason} for url: {response.url}"

        if 300 <= response.status_code < 400:
            http_error_msg = f"{response.status_code} Redirection: {reason} for url: {response.url}"

        if 400 <= response.status_code < 500:
            http_error_msg = f"{response.status_code} Client Error: {reason} for url: {response.url}"

        elif 500 <= response.status_code < 600:
            http_error_msg = f"{response.status_code} Server Error: {reason} for url: {response.url}"

        if http_error_msg:
            raise HTTPError(http_error_msg, response=response)
