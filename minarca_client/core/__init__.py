# Copyright (C) 2021 IKUS Software inc. All rights reserved.
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
import signal
import subprocess
import threading
import time
from datetime import timedelta

import psutil
import rdiff_backup.Main
import rdiff_backup.robust
import requests
from psutil import NoSuchProcess
from rdiff_backup.connection import ConnectionReadError, ConnectionWriteError
from requests.compat import urljoin
from requests.exceptions import ConnectionError, HTTPError, InvalidSchema, MissingSchema

from minarca_client.core import compat
from minarca_client.core.compat import IS_WINDOWS, Scheduler, get_minarca_exe, redirect_ouput, ssh_keygen
from minarca_client.core.config import Datetime, Patterns, Settings, Status
from minarca_client.core.exceptions import (
    BackupError,
    HttpAuthenticationError,
    HttpConnectionError,
    HttpInvalidUrlError,
    HttpServerError,
    NoPatternsError,
    NotConfiguredError,
    NotRunningError,
    NotScheduleError,
    RepositoryNameExistsError,
    RunningError,
    raise_exception,
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


def _escape_remote_shema(path):
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
        return path.replace(' ', '\\ ')


class _UpdateStatus(threading.Thread):
    """
    Update the status while the backup is running.
    """

    def __init__(self, status):
        self.status = status
        super(_UpdateStatus, self).__init__()
        self._stop_event = threading.Event()

    def __enter__(self):
        try:
            if IS_WINDOWS:
                from wakepy import set_keepawake

                set_keepawake(keep_screen_awake=False)
        except Exception:
            pass
        logger.info("backup START")
        self._update_status()
        self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Wait for thread to stop.
        self.stop()
        if exc_type is not KeyboardInterrupt:
            self.join()
        if exc_type is None:
            logger.info("backup SUCCESS")
            self.status['lastresult'] = 'SUCCESS'
            self.status['lastsuccess'] = Datetime()
            self.status['lastdate'] = self.status['lastsuccess']
            self.status['details'] = ''
            self.status.save()
        elif exc_type is KeyboardInterrupt or exc_type is ConnectionWriteError or exc_type is ConnectionReadError:
            # Capture special exception raised when user cancel the operation
            # or when the SSH connection is interrupted.
            logger.exception("backup INTERRUPT")
            self.status['lastresult'] = 'INTERRUPT'
            self.status['lastdate'] = Datetime()
            self.status['details'] = ''
            self.status.save()
        else:
            if isinstance(exc_val, BackupError):
                logger.error("backup FAILED: %s", exc_val)
            else:
                logger.exception("backup FAILED")
            self.status['lastresult'] = 'FAILURE'
            self.status['lastdate'] = Datetime()
            self.status['details'] = str(exc_val)
            self.status.save()
        try:
            if IS_WINDOWS:
                from wakepy import unset_keepawake

                unset_keepawake(keep_screen_awake=False)
        except Exception:
            pass

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

    def start(self, force=False, force_patterns=None, fork=False):
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

        # Fork process if required.
        if fork:
            creationflags = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
                if IS_WINDOWS
                else 0
            )
            p = subprocess.Popen(
                [get_minarca_exe(), 'backup', '--force'],
                stdin=None,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
                creationflags=creationflags,
            )
            return

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
                self._rdiff_backup(args, source=drive)

    def get_patterns(self):
        """
        Return list of include/exclude patterns
        """
        return Patterns(self.patterns_file)

    def get_remote_url(self):
        """
        Return a URL to browse data.
        """
        settings = self.get_settings()
        if IS_WINDOWS:
            # On Windows, we happen a drive letter.
            roots = list(self.get_patterns().group_by_roots())
            if roots:
                drive_letter = roots[0][0][0]
                return "%s/browse/%s/%s/%s" % (
                    settings['remoteurl'],
                    settings['username'],
                    settings['repositoryname'],
                    drive_letter,
                )
            else:
                return settings['remoteurl']
        return "%s/browse/%s/%s" % (settings['remoteurl'], settings['username'], settings['repositoryname'])

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
            elif status['lastdate'] and now - status['lastdate'] > timedelta(seconds=_RUNNING_DELAY + 1):
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
        lastsuccess = self.get_status('lastsuccess')
        if lastsuccess is None:
            return True
        delta = datetime.timedelta(hours=self.get_settings('schedule') * 98.0 / 100)
        return delta < Datetime() - lastsuccess

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
                logger.warning(
                    _('fail to link because repository with name `%s` already exists on remote server')
                    % repository_name
                )
                raise RepositoryNameExistsError(repository_name)

            # Check if ssh keys exists
            if not os.path.exists(self.public_key_file) and not os.path.exists(self.private_key_file):
                logger.debug(_('generating identity'))
                ssh_keygen(self.public_key_file, self.private_key_file)

            # Push SSH Keys
            with open(self.public_key_file) as f:
                logger.debug(_('exchanging identity with minarca server'))
                rdiffweb.add_ssh_key(repository_name, f.read())

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
            self.schedule()
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

        # TODO Update encoding

    def _rdiff_backup(self, extra_args, source=None):
        """
        Make a call to rdiff-backup executable
        """
        # Read config file for remote host
        config = self.get_settings()
        if not config['remotehost']:
            raise NotConfiguredError()
        remote_host, unused, remote_port = config['remotehost'].partition(':')
        repositoryname = config['repositoryname']
        if not config['repositoryname']:
            raise NotConfiguredError()

        # base command line
        args = ['-v', '4', '--remote-schema']
        remote_schema = _escape_remote_shema(compat.get_ssh())
        remote_schema += " -oBatchMode=yes -oPreferredAuthentications=publickey"
        if os.environ.get('MINARCA_ACCEPT_HOST_KEY', False) in ['true', '1', 'True']:
            remote_schema += ' -oStrictHostKeyChecking=no'
        if remote_port:
            remote_schema += ' -p %s' % remote_port
        remote_schema += " -oUserKnownHostsFile='{known_hosts}' -oIdentitiesOnly=yes -i '{identity}' %s '{user_agent_string}'".format(
            known_hosts=self.known_hosts,
            identity=self.private_key_file,
            user_agent_string=compat.get_user_agent(),
        )
        args.append(remote_schema)
        args.extend(extra_args)
        if source:
            args.append(source)
        if IS_WINDOWS and source:
            args.append(
                "minarca@{remote_host}::{repositoryname}/{drive}".format(
                    remote_host=remote_host, repositoryname=repositoryname, drive=source[0]
                )
            )
        else:
            args.append(
                "minarca@{remote_host}::{repositoryname}".format(remote_host=remote_host, repositoryname=repositoryname)
            )

        # Execute the command line.
        logging.debug(_('executing command: %s') % _sh_quote(args))
        try:
            cwd = os.getcwd()
            ld_path = os.environ.get('LD_LIBRARY_PATH')
            if ld_path:
                del os.environ['LD_LIBRARY_PATH']
            os.chdir('..')
            with redirect_ouput(logger):
                # We need to avoid settings signal handlers.
                rdiff_backup.robust.install_signal_handlers = lambda: None
                rdiff_backup.Main.Main(args)
        except SystemExit as e:
            logging.error('rdiff-backup exit with non-zero code')
            raise_exception(e)
        finally:
            os.chdir(cwd)
            if ld_path:
                os.environ['LD_LIBRARY_PATH'] = ld_path

    def schedule(self, schedule=None):
        """
        Create the required schedule job in crontab or windows task scheduler.
        """
        if schedule:
            settings = self.get_settings()
            settings['schedule'] = schedule
            settings.save()
        Scheduler().create(force=True)

    def set_patterns(self, patterns):
        assert isinstance(patterns, list), 'patterns should be a list'
        p = Patterns(self.patterns_file)
        p.clear()
        p.extend(patterns)
        p.save()

    def stop(self):
        """
        Stop the running backup process.
        """
        # Check status for running backup.
        status = self.get_status()
        if status['lastresult'] != 'RUNNING':
            raise NotRunningError()
        # Get pid and checkif process is running.
        try:
            pid = int(status['pid'])
        except ValueError:
            raise NotRunningError()
        p = psutil.Process(pid)
        if not p.is_running():
            raise NotRunningError()
        # Send appropriate signal

        try:
            if IS_WINDOWS:
                # On windows, we need to terminate the process. Ideally, we
                # terminate the ssh connection to clean-up everything properly.
                # It give a chance to minarca to leave cleanly.
                # https://stackoverflow.com/questions/44124338/trying-to-implement-signal-ctrl-c-event-in-python3-6
                for child in p.children(recursive=True):
                    if 'ssh.exe' in child.name():
                        child.terminate()
                        return
                p.terminate()
            else:
                p.send_signal(signal.SIGINT)
        except SystemError:
            logger.debug('error trying to stop minarca', exc_info=1)

    def test_server(self):
        """
        Check connectivity to the remote server using rdiff-backup.
        """
        self._rdiff_backup(['--test-server'])

    def unlink(self):
        """
        Disconnect this client from minarca server.
        """
        config = self.get_settings()
        config['configured'] = False
        config.save()
        # Remove scheduler
        Scheduler().delete()


class Rdiffweb:
    def __init__(self, remote_url, username, password):
        # Create HTTP Session using authentication
        assert username
        assert password
        self.username = username
        self.session = requests.Session()
        self.session.headers['User-Agent'] = compat.get_user_agent()
        self.session.auth = (username, password)
        # Check if connection is working and get redirection if needed
        response = self.session.get(urljoin(remote_url + '/', "api/"))
        response.raise_for_status()
        # Replace remote_URL by using response URL to support redirection.
        if not response.url.endswith('/api/'):
            raise ConnectionError()
        # Trim /api/
        self.remote_url = response.url[0:-4]

    def add_ssh_key(self, title, public_key):
        response = self.session.post(
            self.remote_url + 'prefs/sshkeys/', data={'action': 'add', 'title': title, 'key': public_key}
        )
        response.raise_for_status()

    def get_current_user_info(self):
        response = self.session.get(self.remote_url + 'api/currentuser/')
        response.raise_for_status()
        return response.json()

    def get_minarca_info(self):
        """
        Return a dict with `version`, `remotehost`, `identity`
        """
        response = self.session.get(self.remote_url + 'api/minarca/')
        response.raise_for_status()
        return response.json()
