# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Oct. 13, 2023, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''

import asyncio
import datetime
import fnmatch
import logging
import os
import re
import uuid
from collections import namedtuple
from pathlib import Path

from requests.exceptions import ConnectionError, HTTPError, InvalidSchema, MissingSchema

from minarca_client.core.compat import (
    IS_WINDOWS,
    detach_call,
    file_read_async,
    file_write_async,
    get_config_home,
    get_minarca_exe,
)
from minarca_client.core.config import Datetime, Patterns, Settings
from minarca_client.core.disk import get_location_info
from minarca_client.core.exceptions import (
    DuplicateSettingsError,
    HttpAuthenticationError,
    HttpConnectionError,
    HttpInvalidUrlError,
    HttpServerError,
    InitDestinationError,
    InstanceNotFoundError,
    InvalidRepositoryName,
    LocalDestinationNotEmptyError,
    RepositoryNameExistsError,
)
from minarca_client.core.instance import BackupInstance
from minarca_client.core.rdiffweb import Rdiffweb
from minarca_client.core.scheduler import Scheduler

if IS_WINDOWS:
    import win32api
    import win32con

_REPOSITORY_NAME_PATTERN = "^[a-zA-Z0-9][a-zA-Z0-9\\-\\.]*$"

logger = logging.getLogger(__name__)

InstanceId = namedtuple('InstanceId', 'value')


def _check_repositoryname(name):
    if not re.match(_REPOSITORY_NAME_PATTERN, name):
        raise InvalidRepositoryName(name)


class Backup:
    """
    Collection of backup instances based on "minarca*.properties" files.
    """

    def __init__(self):
        """
        Create a new minarca backup.
        """
        self.scheduler = Scheduler()
        self._config_home = get_config_home()

    def _entries(self):
        """Return list of config files"""
        return [fn for fn in os.listdir(self._config_home) if fnmatch.fnmatch(fn, "minarca*.properties")]

    def __iter__(self):
        """
        Return an iterator on backup instances.
        """
        filenames = sorted(self._entries())
        return iter([BackupInstance(fn[7:-11]) for fn in filenames])

    def __len__(self):
        return len(self._entries())

    def __bool__(self):
        # Required for assert
        return True

    def __getitem__(self, key):
        assert isinstance(key, int) or isinstance(key, InstanceId) or isinstance(key, str)
        if isinstance(key, int):
            # If key is an integer, this is the index value
            filenames = sorted(self._entries())
            fn = filenames[key]
            num = fn[7:-11]
            return BackupInstance(num)
        if isinstance(key, str):
            # If key is a string, this is the "num"
            instance = BackupInstance(key)
            if instance not in self:
                raise InstanceNotFoundError(key)
            return instance
        # If key is a list, return list of corresponding instances.
        if isinstance(key, InstanceId):
            if key.value is None:
                return list(self)
            criterias = key.value.split(',')
            # TODO Add more matching criteria. e.g.: remoteurl
            instances = [instance for instance in self if str(instance.id) in criterias]
            # Raise error if nothing matches our instance_id.
            if not instances:
                raise InstanceNotFoundError(key.value)
            return instances

    def __contains__(self, other):
        assert isinstance(other, BackupInstance)
        return ("minarca%s.properties" % other.id) in self._entries()

    def start_all(self, action='backup', force=False, patterns=None, instance_id=None):
        logger.debug(
            f"starting all backups with action: {action}, force: {force}, patterns: {patterns}, instance_id: {instance_id}"
        )
        assert action in ['backup', 'restore']
        # Fork process
        args = [get_minarca_exe(), action]
        if force:
            args += ['--force']
        if instance_id:
            args += ['--instance', str(instance_id)]
        if patterns:
            assert action == 'restore'
            args += [p.pattern for p in patterns]
        child = detach_call(args)
        logger.debug(f'subprocess {child.pid} started')

    def schedule_job(self, run_if_logged_out=None, replace=True):
        """
        Used to schedule the job in operating system task scheduler. e.g.: crontab.

        On Windows, username and password are required if we want to run the task whenever the user is logged out.
        `run_if_logged_out` should then contain a tuple with username and password.
        """
        logger.debug("scheduling job in OS task scheduler")
        # Also schedule task in Operating system scheduler.
        exists = self.scheduler.exists()
        if replace and exists:
            logger.debug("scheduler exists, replacing existing schedule")
            self.scheduler.delete()
        elif exists:
            return  # Do nothing
        if IS_WINDOWS:
            self.scheduler.create(run_if_logged_out=run_if_logged_out)
        else:
            self.scheduler.create()

    def is_configured(self):
        """
        Return true if any of the backup instances is properly configured.
        """
        logger.debug("checking if any backup instance is configured")
        return any(instance.settings.configured for instance in self)

    async def configure_local(self, path, repositoryname, force=False, instance=None):
        """
        Used to configure this new or existing instance with a local disk.

        To configure a local disk, this function will generate a unique UUID
        file in a specific location to be searched for when trying to backup.

        <mountpoint>/<path>/../.minarca-<localuuid>
        """
        logger.debug(f"configuring local instance with path: {path}, repositoryname: {repositoryname}, force: {force}")
        assert isinstance(path, (str, Path))
        path = Path(path) if isinstance(path, str) else path
        # Validate the repository name
        _check_repositoryname(repositoryname)

        # Get detail information about the destination
        disk_info = get_location_info(path)

        # Check if duplicate of current settings
        uuid_fn = path.parent / '.minarca-id'
        localuuid = await file_read_async(uuid_fn)
        if localuuid:
            others = [
                other
                for other in self
                if other.is_local()
                and other.settings.localuuid == localuuid
                and other.settings.localrelpath == disk_info.relpath
                and other.settings.repositoryname == repositoryname
            ]
            if others:
                raise DuplicateSettingsError(others[0])

        # Make sure the destination is an empty folder or an existing backup.
        content = list(path.iterdir())
        if content:
            if IS_WINDOWS:
                # Take into account Windows Drive letter
                existing_backup = all([[len(f.name) == 1 and (f / 'rdiff-backup-data').exists for f in path.iterdir()]])
            else:
                existing_backup = (path / 'rdiff-backup-data').exists()
            if not existing_backup:
                raise LocalDestinationNotEmptyError(path)
            elif not force:
                reponame = path.name
                raise RepositoryNameExistsError(reponame)

        # Generate a diskuuid if missing
        if localuuid is None:
            localuuid = str(uuid.uuid4())
            try:
                # Create missing directory structure
                uuid_fn.parent.mkdir(exist_ok=1)
                # Create uuid file
                await file_write_async(uuid_fn, localuuid)
                # Hide the file and make it readonly.
                if IS_WINDOWS:
                    win32api.SetFileAttributes(
                        str(uuid_fn), win32con.FILE_ATTRIBUTE_READONLY | win32con.FILE_ATTRIBUTE_HIDDEN
                    )
                else:
                    os.chmod(uuid_fn, 0o444)
            except OSError:
                raise InitDestinationError()

        # Create or update instance
        instance = self._new_instance() if instance is None else instance

        # Define default patterns if none are defined.
        if len(list(instance.patterns.group_by_roots())) == 0:
            instance.patterns.extend(Patterns.defaults())

        # Clear previous status file
        instance.status.clear()

        # Save configuration
        with instance.settings as t:
            t.repositoryname = repositoryname
            t.localuuid = localuuid
            t.localrelpath = disk_info.relpath
            t.localmountpoint = disk_info.mountpoint
            t.localcaption = disk_info.caption
            t.schedule = Settings.DAILY
            # Pause 1 hour to avoid getting started while configuring.
            t.pause_until = Datetime() + datetime.timedelta(hours=1)
            # Save configuration
            t.configured = True

        logger.debug(f"local instance configured: {instance.id}")
        return instance

    async def configure_remote(self, remoteurl, username, password, repositoryname, force=False, instance=None):
        """
        Use to configure new or existing instance for remote backup

        Set `force` to True to link even if the repository name already exists.
        """
        logger.debug(
            f"Configuring remote instance with URL: {remoteurl}, username: {username}, repositoryname: {repositoryname}, force: {force}"
        )
        # Validate the repository name
        _check_repositoryname(repositoryname)

        try:
            # Connect to remote server to get more information.
            conn = Rdiffweb(remoteurl)
            conn.auth = (username, password)
            current_user = await asyncio.get_running_loop().run_in_executor(None, conn.get_current_user_info)

            # Check if the settings already exist.
            others = [
                other
                for other in self
                if other.is_remote()
                and other.settings.remoteurl == conn.remoteurl
                and other.settings.repositoryname == repositoryname
                and other.settings.username == username
            ]
            if others:
                raise DuplicateSettingsError(others[0])

            # Then check if the repo name already exists remotely.
            exists = [
                r
                for r in current_user.get('repos', [])
                if repositoryname == r.get('name') or r.get('name').startswith(repositoryname + '/')
            ]
            if not force and exists:
                raise RepositoryNameExistsError(repositoryname)

            # Create or update instance
            instance = self._new_instance() if instance is None else instance

            # Generate SSH Keys
            await instance._push_identity(conn, repositoryname)

            # Store minarca identity
            minarca_info = await asyncio.get_running_loop().run_in_executor(None, conn.get_minarca_info)
            await file_write_async(instance.known_hosts, minarca_info['identity'])

            # Create default config
            instance.settings.username = username
            instance.settings.repositoryname = repositoryname
            instance.settings.remotehost = minarca_info['remotehost']
            instance.settings.remoteurl = remoteurl
            instance.settings.schedule = Settings.DAILY

            # Only test the connection
            await instance.test_connection()

            # Define default patterns if none are defined.
            if len(list(instance.patterns.group_by_roots())) == 0:
                instance.patterns.extend(Patterns.defaults())

            # Clear previous status file
            instance.status.clear()

            # For data consistency. Also store existing configuration if repo exists.
            if exists:
                data = exists[0]
                if 'maxage' in data:
                    instance.settings.maxage = int(data['maxage'])
                if 'keepdays' in data:
                    instance.settings.keepdays = int(data['keepdays'])
                if 'ignore_weekday' in data and isinstance(data['ignore_weekday'], list):
                    instance.settings.ignore_weekday = data['ignore_weekday']
                if 'role' in current_user:
                    instance.settings.remoterole = int(current_user['role'])

            # Pause 1 hour to avoid getting started while configuring.
            instance.settings.pause_until = Datetime() + datetime.timedelta(hours=1)
            # Save configuration
            instance.settings.configured = True
            instance.settings.save()
            logger.debug(f"remote instance configured: {instance.id}")
        except ConnectionError:
            # Raised with invalid URL or port
            raise HttpConnectionError(remoteurl)
        except (MissingSchema, InvalidSchema):
            raise HttpInvalidUrlError(remoteurl)
        except HTTPError as e:
            # Raise for invalid status code.
            if e.response.status_code in [401, 403]:
                raise HttpAuthenticationError(e)
            raise HttpServerError(e)
        return instance

    def _new_instance(self):
        """
        Create a new instance of Backup without configuration.
        """
        try:
            idx = int(self[-1].id) if len(self) else 0
        except ValueError:
            idx = 0
        while True:
            instance = BackupInstance(idx)
            if instance in self:
                idx += 1
                continue
            return instance

    async def awatch(self, poll_delay_ms=250):
        """
        Return changes whenever the file gets updated.
        """
        logger.debug(f"starting async watch with poll delay: {poll_delay_ms} ms")
        prev_entries = self._entries()
        while True:
            await asyncio.sleep(poll_delay_ms / 1000)
            new_entries = self._entries()
            if prev_entries != new_entries:
                logger.debug("backup instances updated")
                yield "changed"
            prev_entries = new_entries
