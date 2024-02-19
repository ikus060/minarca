# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Oct. 13, 2023, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''

import asyncio
import fnmatch
import logging
import os
import re
import uuid
from collections import namedtuple

from requests.exceptions import ConnectionError, HTTPError, InvalidSchema, MissingSchema

from minarca_client.core.compat import IS_WINDOWS, Scheduler, detach_call, file_read, get_config_home, get_minarca_exe
from minarca_client.core.config import Patterns, Settings
from minarca_client.core.disk import get_disk_info
from minarca_client.core.exceptions import (
    LocalDestinationNotEmptyError,
    DuplicateSettingsError,
    HttpAuthenticationError,
    HttpConnectionError,
    HttpInvalidUrlError,
    HttpServerError,
    InitDestinationError,
    InstanceNotFoundError,
    InvalidRepositoryName,
    RepositoryNameExistsError,
)
from minarca_client.core.instance import BackupInstance
from minarca_client.core.rdiffweb import Rdiffweb

_REPOSITORY_NAME_PATTERN = "^[a-zA-Z0-9][a-zA-Z0-9\\-\\.]*$"

logger = logging.getLogger(__name__)

limit = namedtuple('limit', 'value')


def _check_repositoryname(name):
    if not re.match(_REPOSITORY_NAME_PATTERN, name):
        raise InvalidRepositoryName(name)


class Backup:
    """
    Collection of backup instances base on "minarca*.properties" files.
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
        return [BackupInstance(fn[7:-11]) for fn in filenames].__iter__()

    def __len__(self):
        return len(self._entries())

    def __getitem__(self, key):
        assert isinstance(key, int) or isinstance(key, limit) or isinstance(key, str)
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
        if isinstance(key, limit):
            if key.value is None:
                return list(self)
            criterias = key.value.split(',')
            # TODO Add more matching criteria. e.g.: remoteurl
            instances = [instance for instance in self if str(instance.id) in criterias]
            # Raise error is nothing matches our limit.
            if not instances:
                raise InstanceNotFoundError(key.value)
            return instances

    def __contains__(self, other):
        assert isinstance(other, BackupInstance)
        return ("minarca%s.properties" % other.id) in self._entries()

    def start_all(self, action='backup', force=False, patterns=None, limit=None):
        assert action in ['backup', 'restore']
        # Fork process
        args = [get_minarca_exe(), action]
        if force:
            args += ['--force']
        if limit:
            args += ['--limit', str(limit)]
        if patterns:
            assert action == 'restore'
            args += [p.pattern for p in patterns]
        child = detach_call()
        logger.info('subprocess %s started' % child.pid)

    def get_help_url(self):
        """
        Return the first non null help URL. Or return default mianrca URL.
        """
        for instance in self:
            url = instance.get_help_url()
            if url:
                return url
        return 'https://minarca.org/contactus'

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

    def forget(self):
        """
        Forget all settings.
        """
        for instance in list(self):
            instance.forget()

    def is_configured(self):
        """
        Return true if any of the backup instance is property configured.
        """
        return any(instance.settings.configured for instance in self)

    def configure_local(self, path, repositoryname, force=False, instance=None):
        """
        Used to configure this new or existing instance with a local disk.

        To configure a local disk, this function will generate a unique UUID
        file in a specific location to be searched for when trying to backup.

        <mountpoint>/<path>/../.minarca-<localuuid>
        """
        assert os.path.isdir(path), 'path must be a folder'
        # Validate the repository name
        _check_repositoryname(repositoryname)

        # Get detail information about the destination
        disk_info = get_disk_info(path)
        if disk_info is None:
            # TODO Should get fixed.
            raise ValueError('not a block device')

        # Check if duplicate of current settings
        uuid_fn = os.path.join(disk_info.mountpoint, disk_info.relpath, '..', '.minarca-id')
        localuuid = file_read(uuid_fn)
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

        # Make sure the destination is an empty folder.
        content = os.listdir(path)
        if content:
            if 'rdiff-backup-data' not in content:
                raise LocalDestinationNotEmptyError(path)
            elif not force:
                reponame = os.path.basename(path)
                raise RepositoryNameExistsError(reponame)

        # Generate a diskuuid if missing
        if localuuid is None:
            try:
                # Create missing directory structure
                os.makedirs(os.path.join(path, '..'), exist_ok=1)
                # Create uuid file
                with open(uuid_fn, 'w') as f:
                    localuuid = str(uuid.uuid4())
                    f.write(localuuid)
                # TODO Hide the file and make it readonly.
            except OSError:
                raise InitDestinationError()

        # Create or update instance
        instance = self._new_instance() if instance is None else instance

        # Define default patterns if none are define.
        if len(list(instance.patterns.group_by_roots())) == 0:
            instance.patterns.extend(Patterns.defaults())

        # Clear previous status file
        instance.status.clear()

        # Save configuration
        with instance.settings as t:
            t.repositoryname = repositoryname
            t.localuuid = localuuid
            t.localrelpath = disk_info.relpath
            t.localcaption = disk_info.caption
            t.schedule = Settings.DAILY
            # Save configuration
            t.configured = True

        return instance

    def configure_remote(self, remoteurl, username, password, repositoryname, force=False, instance=None):
        """
        Use to configure new or existing instance for remote backup

        Set `force` to True to link event if the repository name already exists.
        """
        # Validate the repository name
        _check_repositoryname(repositoryname)

        try:
            # Connect to remote server to get more information.
            conn = Rdiffweb(remoteurl)
            conn.auth = (username, password)
            current_user = conn.get_current_user_info()

            # Check if the settings already exists.
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
            exists = any(
                repositoryname == r.get('name') or r.get('name').startswith(repositoryname + '/')
                for r in current_user.get('repos', [])
            )
            if not force and exists:
                raise RepositoryNameExistsError(repositoryname)

            # Create or update instance
            instance = self._new_instance() if instance is None else instance

            # Generate SSH Keys
            instance._push_identity(conn, repositoryname)

            # Store minarca identity
            minarca_info = conn.get_minarca_info()
            with open(instance.known_hosts, 'w') as f:
                f.write(minarca_info['identity'])

            # Create default config
            with instance.settings as t:
                t.username = username
                t.repositoryname = repositoryname
                t.remotehost = minarca_info['remotehost']
                t.remoteurl = remoteurl
                t.schedule = Settings.DAILY

            # Only test the connection
            instance.test_connection()

            # Define default patterns if none are define.
            if len(list(instance.patterns.group_by_roots())) == 0:
                instance.patterns.extend(Patterns.defaults())

            # Clear previous status file
            instance.status.clear()

            # Save configuration
            instance.settings.configured = True
            instance.settings.save()
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

    def check_duplicate(self, instance):
        """
        Check if the given instance has a dusplicate instance.
        """

        def eq(a, b):
            if a.is_remote():
                return (
                    b.is_remote()
                    and a.settings.repositoryname == b.settings.repositoryname
                    and a.settings.remoteurl == b.settings.remoteurl
                    and a.settings.username == b.settings.username
                )
            elif a.is_local():
                return (
                    b.is_local()
                    and a.settings.localuuid == b.settings.localuuid
                    and a.settings.localrelpath == b.settings.localrelpath
                )
            return False

        for other in self:
            if other is instance:
                # Do not compare to our self.
                continue
            if eq(other, instance):
                return other
        return None

    async def awatch(self, poll_delay_ms=250):
        """
        Return changes whenever the file get updated.
        """
        prev_entries = self._entries()
        while True:
            await asyncio.sleep(poll_delay_ms / 1000)
            new_entries = self._entries()
            if prev_entries != new_entries:
                yield "changed"
            prev_entries = new_entries
