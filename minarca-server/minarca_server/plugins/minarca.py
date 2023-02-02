# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import logging
import os
import stat
import subprocess
from io import StringIO, open

import cherrypy
import requests
from cherrypy.process.plugins import SimplePlugin
from rdiffweb.core import authorizedkeys
from rdiffweb.core.authorizedkeys import AuthorizedKey
from rdiffweb.core.config import Option
from rdiffweb.core.model import UserObject

# Define logger for this module
logger = logging.getLogger(__name__)


class TimeoutHTTPAdapter(requests.adapters.HTTPAdapter):
    def send(self, *args, **kwargs):
        # Enforce a timeout value if not defined.
        kwargs['timeout'] = kwargs.get('timeout', None)
        return super(TimeoutHTTPAdapter, self).send(*args, **kwargs)


class MinarcaPlugin(SimplePlugin):
    """
    This plugin provide feedback information to the users about the disk usage.
    Since we define quota, this plugin display the user's quota.
    """

    _log_file = Option('log_file')
    _log_access_file = Option('log_access_file')

    user_dir_mode = 0o0770
    user_dir_owner_id = 65534  # nobody
    user_dir_group_id = 65534  # nobody
    user_base_dir = '/backups'
    shell = '/opt/minarca-server/bin/minarca-shell'
    auth_options = 'no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty'
    remote_host = None
    remote_host_identity = '/etc/ssh'
    restricted_to_base_dir = True
    help_url = 'https://www.ikus-soft.com/en/support/#form'
    quota_api_url = None

    @property
    def app(self):
        return cherrypy.tree.apps['']

    @property
    def session(self):
        if not hasattr(self, '_session'):
            self._session = requests.Session()
            self._session.mount('https://', TimeoutHTTPAdapter(pool_connections=2, pool_maxsize=5))
            self._session.mount('http://', TimeoutHTTPAdapter(pool_connections=2, pool_maxsize=5))
        return self._session

    def start(self):
        self.bus.log('Start Minarca plugin')
        self.bus.subscribe('user_added', self.user_added)
        self.bus.subscribe('user_attr_changed', self.user_attr_changed)
        self.bus.subscribe('user_deleted', self.user_deleted)
        if self.quota_api_url:
            self.bus.subscribe("set_disk_quota", self.set_disk_quota)
            self.bus.subscribe("get_disk_quota", self.get_disk_quota)
            self.bus.subscribe("get_disk_usage", self.get_disk_usage)
        else:
            cherrypy.quota.start()

        # Monkey patch get_log_file
        self._orig_get_log_files = self.app.root.admin.logs._get_log_files
        self.app.root.admin.logs._get_log_files = self._get_log_files
        # On startup Upgrade the authorized_keys in case the configuration
        # changed.
        try:
            self._update_authorized_keys()
        except Exception:
            logger.error("fail to update authorized_keys files on startup", exc_info=1)

    def stop(self):
        self.bus.log('Stop Minarca plugin')
        self.bus.unsubscribe('user_attr_changed', self.user_attr_changed)
        self.bus.unsubscribe('user_attr_changed', self.user_attr_changed)
        self.bus.unsubscribe('user_deleted', self.user_deleted)
        if self.quota_api_url:
            self.bus.unsubscribe("set_disk_quota", self.set_disk_quota)
            self.bus.unsubscribe("get_disk_quota", self.get_disk_quota)
            self.bus.unsubscribe("get_disk_usage", self.get_disk_usage)
        else:
            cherrypy.quota.stop()

        # Remove get_log_file
        self.app.root.admin.logs._get_log_files = self._orig_get_log_files

    def _get_log_files(self):
        """
        Patched version of _get_log_files
        """
        # Add minarca-shell to logfile view.
        minarca_shell_logfile = os.path.join(
            os.path.dirname(self._log_file or '/var/log/minarca/server.log'), 'shell.log'
        )
        logfiles = self._orig_get_log_files()
        logfiles.append(minarca_shell_logfile)
        return logfiles

    def user_added(self, userobj):
        """
        When added (manually or not). Update user's attributes.
        """
        assert isinstance(userobj, UserObject)
        try:
            userobj.user_root = self._get_user_root(userobj)
            self._create_user_root(userobj)
            userobj.refresh_repos(delete=True)
        except Exception:
            logger.warning('fail to update user [%s] root', userobj.username, exc_info=1)

    def user_attr_changed(self, userobj, attrs={}):
        """
        Listen to users attributes change to update the minarca authorized_keys.
        """
        if 'user_root' in attrs:
            user_root = self._get_user_root(userobj)
            if attrs['user_root'][1] != user_root:
                userobj.user_root = user_root

        # Update minarca's authorized_keys when users update their ssh keys.
        if 'authorizedkeys' in attrs or 'user_root' in attrs:
            try:
                self._update_authorized_keys()
            except Exception:
                logger.error("fail to update authorized_keys files on user_attr_changed", exc_info=1)

    def user_deleted(self, username):
        """
        When user get deleted, update the authorized_key.
        """
        try:
            self._update_authorized_keys()
        except Exception:
            logger.error("fail to update authorized_keys files on user_deleted", exc_info=1)

    def _get_user_root(self, userobj):
        """
        Called to update the user's home directory. Either to define it with
        default value or restrict it to base dir.
        """
        # Define default user_home if not provided
        user_root = userobj.user_root or os.path.join(self.user_base_dir, userobj.username)
        # Normalise path to avoid relative path.
        user_root = os.path.abspath(user_root)
        # Verify if the user_root is inside base dir.
        if self.restricted_to_base_dir and not user_root.startswith(self.user_base_dir):
            logger.warning('restrict user [%s] to base dir [%s]', userobj.username, self.user_base_dir)
            user_root = os.path.join(self.user_base_dir, userobj.username)
        return user_root

    def _create_user_root(self, userobj):
        """
        Called to create the user_root folder.
        """
        # Create folder if inside our base dir and missing.
        user_root = userobj.user_root
        if user_root.startswith(self.user_base_dir) and not os.path.exists(user_root):
            logger.info('creating user [%s] root dir [%s]', userobj.username, user_root)
            try:
                os.mkdir(user_root)
                # Change mode
                os.chmod(user_root, self.user_dir_mode)
                # Change owner
                os.chown(user_root, self.user_dir_owner_id, self.user_dir_group_id)
            except Exception:
                logger.warning('fail to create user [%s] root dir [%s]', userobj.username, user_root)

    def _update_authorized_keys(self):
        """
        Used to update the authorized_keys of minarca user.
        """

        # Create ssh subfolder
        ssh_dir = os.path.join(self.user_base_dir, '.ssh')
        if not os.path.exists(ssh_dir):
            logger.info("creating .ssh folder [%s]", ssh_dir)
            os.mkdir(ssh_dir, 0o700)

        os.chown(ssh_dir, self.user_dir_owner_id, self.user_dir_group_id)

        # Create the authorized_keys file
        filename = os.path.join(ssh_dir, 'authorized_keys')
        if not os.path.exists(filename):
            logger.info("creating authorized_keys [%s]", filename)
            with open(filename, 'w+'):
                os.utime(filename, None)
                # change file permissions
                os.chmod(filename, stat.S_IRUSR | stat.S_IWUSR)
                val = os.stat(ssh_dir)
                # Also try to change owner
                os.chown(filename, val.st_uid, val.st_gid)

        # Get list of keys
        seen = set()
        new_data = StringIO()
        for userobj in UserObject.query.all():
            for key in userobj.authorizedkeys:
                if key.fingerprint in seen:
                    logger.warning("duplicates key %s, sshd will ignore it")
                else:
                    seen.add(key.fingerprint)

                # Add option to the key

                options = """command="export MINARCA_USERNAME='{username}' MINARCA_USER_ROOT='{user_root}';{minarca_shell}",{auth_options}""".format(
                    minarca_shell=self.shell,
                    username=userobj.username,
                    user_root=userobj.user_root,
                    auth_options=self.auth_options,
                )

                key = AuthorizedKey(options=options, keytype=key.keytype, key=key.key, comment=key.comment)

                # Write the new key
                authorizedkeys.add(new_data, key)

        # Write the new file
        logger.info("updating authorized_keys file [%s]", filename)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_data.getvalue())

    def get_disk_usage(self, userobj):
        """
        Return the user disk space.
        """
        assert isinstance(userobj, UserObject)
        # Get Quota from web service
        url = os.path.join(self.quota_api_url, 'quota', str(userobj.userid))
        try:
            r = self.session.get(url, timeout=1)
            r.raise_for_status()
            diskspace = r.json()
            return diskspace['used']
        except Exception:
            logger.warning('fail to get user quota [%s]', userobj.username, exc_info=1)
            return 0

    def get_disk_quota(self, userobj):
        """
        Get's user's disk quota.
        """
        # Get Quota from web service
        url = os.path.join(self.quota_api_url, 'quota', str(userobj.userid))
        try:
            r = self.session.get(url, timeout=1)
            r.raise_for_status()
            diskspace = r.json()
            return diskspace['size']
        except Exception:
            logger.warning('fail to get user quota [%s]', userobj.username, exc_info=1)
            return 0

    def set_disk_quota(self, userobj, quota):
        """
        Sets the user's quota.
        """
        # Always update unless quota not define
        try:
            logger.info('set user [%s] quota [%s]', userobj.username, quota)
            url = os.path.join(self.quota_api_url, 'quota', str(userobj.userid))
            r = self.session.post(url, data={'size': quota}, timeout=1)
            r.raise_for_status()
        except Exception:
            logger.warning("fail to update user root quota", exc_info=1)
            return False

        # Schedule update attribute task in background
        cherrypy.engine.publish('schedule_task', self._update_attr_task, userobj.user_root, userobj.userid)

        return quota

    def _update_attr_task(self, user_root, project_id):
        # Update user root attribute
        try:
            # Add +P attribute to user's home directory
            subprocess.check_output(
                ["/usr/bin/chattr", "-R", "+P", "-p", str(project_id), user_root], stderr=subprocess.STDOUT
            )
        except Exception:
            logger.warning("fail to update user quota", exc_info=1)


cherrypy.minarca = MinarcaPlugin(cherrypy.engine)
cherrypy.minarca.subscribe()
cherrypy.quota.unsubscribe()

cherrypy.config.namespaces['minarca'] = lambda key, value: setattr(cherrypy.minarca, key, value)
