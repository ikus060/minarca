# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Oct. 13, 2023, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''

import asyncio
import datetime
import logging
import re
import uuid
from collections import namedtuple
from pathlib import Path
from typing import Dict

from minarca_client.core.compat import (
    IS_WINDOWS,
    detach_call,
    file_read_async,
    file_write_async,
    get_config_home,
    get_data_home,
    get_minarca_exe,
    rmtree,
    secure_file,
)
from minarca_client.core.exceptions import (
    DuplicateSettingsError,
    InitDestinationError,
    InstanceNotFoundError,
    InvalidRepositoryName,
    LocalDestinationNotEmptyError,
    RepositoryNameExistsError,
    handle_http_errors,
)
from minarca_client.core.instance import BackupInstance
from minarca_client.core.pattern import Patterns
from minarca_client.core.scheduler import Scheduler
from minarca_client.core.settings import Datetime, Settings

_REPOSITORY_NAME_PATTERN = "^[a-zA-Z0-9][a-zA-Z0-9\\-\\.]*$"

logger = logging.getLogger(__name__)

InstanceId = namedtuple('InstanceId', 'value')

INSTANCE_RE = re.compile(r"^minarca(\d*)\.properties$")


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
        self._data_home = get_data_home()
        self._instances: Dict[str, BackupInstance] = {}
        self.rescan()

    # Discover minarcaN.properties; statusN.properties are optional.
    def rescan(self) -> None:
        found_ids = {
            m.group(1) for p in self._config_home.iterdir() if p.is_file() and (m := INSTANCE_RE.match(p.name))
        }
        # Remove deleted
        for id in set(self._instances) - found_ids:
            self._instances.pop(id, None)
        # Add new and refresh props+status for all
        for id in sorted(found_ids):
            inst = self._instances.get(id) or BackupInstance(self._config_home, self._data_home, id)
            inst.load_status()
            inst.load_settings()
            inst.load_patterns()
            self._instances[id] = inst

    def __iter__(self):
        """
        Return an iterator on backup instances.
        """
        return iter(self._instances.values())

    def __len__(self):
        return len(self._instances)

    def __bool__(self):
        # Required for assert
        return True

    def __getitem__(self, key):
        assert (
            isinstance(key, int)
            or isinstance(key, InstanceId)
            or isinstance(key, str)
            or isinstance(key, BackupInstance)
        )
        if isinstance(key, int):
            # If key is an integer, this is the index value
            ids = sorted(set(self._instances))
            id = ids[key]
            return self._instances[id]
        if isinstance(key, str):
            # If key is a string, this is the "num"
            if key not in self._instances:
                raise InstanceNotFoundError(key)
            return self._instances[key]
        # If key is a list, return list of corresponding instances.
        if isinstance(key, InstanceId):
            if key.value is None:
                return list(self)
            criterias = key.value.split(',')
            # TODO Add more matching criteria. e.g.: remoteurl
            instances = [instance for instance in self._instances.values() if str(instance.id) in criterias]
            # Raise error if nothing matches our instance_id.
            if not instances:
                raise InstanceNotFoundError(key.value)
            return instances
        if isinstance(key, BackupInstance):
            return self._instances[key.id]

    def __contains__(self, other):
        assert isinstance(other, BackupInstance)
        return other.id in self._instances

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

    async def configure_local(self, path, repositoryname, force=False, purge_destination=False, instance=None):
        """
        Used to configure this new or existing instance with a local disk.

        To configure a local disk, this function will generate a unique UUID
        file in a specific location to be searched for when trying to backup.

        <mountpoint>/<path>/../.minarca-<localuuid>
        """
        from minarca_client.core.disk import get_location_info

        logger.debug(
            f"configuring local instance with path: {path}, repositoryname: {repositoryname}, force: {force}, purge_destination: {purge_destination}"
        )
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
            if purge_destination:
                rmtree(path)
            else:
                if IS_WINDOWS:
                    # On Windows, take into account Windows Drive letter
                    existing_backup = all([(file / 'rdiff-backup-data').exists() for file in content])
                else:
                    existing_backup = (path / 'rdiff-backup-data').exists()
                if not existing_backup:
                    raise LocalDestinationNotEmptyError(path, content)
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
                secure_file(uuid_fn, 0o444)
            except OSError:
                raise InitDestinationError()

        # Create or update instance
        instance = self._new_instance() if instance is None else instance

        # Define default patterns if none are defined.
        if len(instance.patterns) == 0:
            instance.patterns.extend(Patterns.defaults())

        # Clear previous status file
        instance.status.clear()

        # Save configuration
        s = instance.settings
        s.repositoryname = repositoryname
        s.localuuid = localuuid
        s.localrelpath = disk_info.relpath
        s.localmountpoint = disk_info.mountpoint
        s.localcaption = disk_info.caption
        s.schedule = Settings.DAILY
        # Pause 1 hour to avoid getting started while configuring.
        s.pause_until = Datetime() + datetime.timedelta(hours=1)
        # Save configuration
        s.configured = True

        instance.save_status()
        instance.save_patterns()
        instance.save_settings()

        logger.debug(f"local instance configured: {instance.id}")
        return instance

    @handle_http_errors
    async def configure_remote(self, remoteurl, username, password, repositoryname, force=False, instance=None):
        """
        Use to configure new or existing instance for remote backup

        Set `force` to True to link even if the repository name already exists.
        """
        from minarca_client.core.rdiffweb import Rdiffweb

        logger.debug(
            f"Configuring remote instance with URL: {remoteurl}, username: {username}, repositoryname: {repositoryname}, force: {force}"
        )
        # Validate the repository name
        _check_repositoryname(repositoryname)

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
        if len(instance.patterns) == 0:
            instance.patterns.extend(Patterns.defaults())
        instance.save_patterns()

        # Clear previous status file
        instance.status.clear()
        instance.save_status()

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
        instance.save_settings()
        logger.debug(f"remote instance configured: {instance.id}")

        return instance

    def _next_free_id(self) -> int:
        n = 0
        while n in self._instances:
            n += 1
        return n

    def _new_instance(self) -> BackupInstance:
        iid = self._next_free_id()
        inst = BackupInstance(self._config_home, self._data_home, iid)
        self._instances[iid] = inst
        return inst

    def delete_instance(self, key) -> None:
        instances = self.__getitem__(key)
        instances = instances if hasattr(instances, '__iter__') else [instances]
        for inst in instances:
            for p in (
                inst.status_file,
                inst.patterns_file,
                inst.backup_log_file,
                inst.restore_log_file,
                inst.settings_file,
                inst.public_key_file,
                inst.private_key_file,
                inst.known_hosts,
            ):
                try:
                    secure_file(p, mode=0o600)
                    p.unlink(missing_ok=True)
                except Exception:
                    pass
            self._instances.pop(inst.id)

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
            self.settings_file,
        ]:
            if not fn.is_file():
                continue
            try:
                secure_file(fn, mode=0o600)
                fn.unlink()
                logger.debug(f"{self.log_id}: deleted file: {fn}")
            except OSError:
                logger.warning(f"{self.log_id}: cannot delete file: {fn}", exc_info=1)

    async def awatch(self, poll_delay_ms=250):
        """
        Return changes whenever the file gets updated.
        """
        logger.debug(f"starting async watch with poll delay: {poll_delay_ms} ms")
        files = set(self._config_home.iterdir())
        while True:
            await asyncio.sleep(poll_delay_ms / 1000)
            new_files = set(self._config_home.iterdir())
            if files != new_files:
                logger.debug("backup instances updated")
                yield "changed"
            files = new_files
