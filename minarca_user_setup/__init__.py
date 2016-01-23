#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca disk space rdiffweb plugin
#
# Copyright (C) 2015 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import unicode_literals

import distutils.spawn
from builtins import str
from future.utils.surrogateescape import decodefilename, encodefilename
import logging
import os
import pwd
from subprocess import Popen
import subprocess
import sys

from rdiffweb.core import RdiffError
from rdiffweb.rdw_plugin import IRdiffwebPlugin, IUserChangeListener


logger = logging.getLogger(__name__)


PY3 = sys.version_info[0] == 3


class MinarcaUserSetup(IUserChangeListener):

    @property
    def _mode(self):
        return self.app.cfg.get_config_int('MinarcaUserSetupDirMode', 0o0700)

    @property
    def _basedir(self):
        return self.app.cfg.get_config('MinarcaUserSetupBaseDir', '/home')

    @property
    def _zfs_pool(self):
        return self.app.cfg.get_config('MinarcaUserSetupZfsPool')

    def _create_user_root(self, user, user_root):
        """Create and configure user home directory"""

        # Get User / Group id
        try:
            pwd_user = self._getpwnam(user)
            uid = pwd_user.pw_uid
            gid = pwd_user.pw_gid
        except KeyError:
            uid = -1
            gid = -1

        # Create folder if missing
        if not os.path.exists(user_root):
            logger.info('creating user [%s] root dir [%s]', user, user_root)
            os.makedirs(user_root, mode=self._mode)
            os.chown(user_root, uid, gid)

        if not os.path.isdir(user_root):
            raise RdiffError(_('fail to create user [%s] root dir [%s]', user, user_root))

        # Create ssh subfolder
        ssh_dir = os.path.join(user_root, '.ssh')
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, mode=0o0700)
            os.chown(ssh_dir, uid, gid)

    def get_ldap_store(self):
        """get reference to ldap_store"""
        plugin = self.app.plugins.get_plugin_by_name('Ldap')
        if plugin:
            return plugin.plugin_object
        return None

    def get_ldap_userquota(self, user):
        """Get userquota from LDAP database."""
        assert isinstance(user, str)

        # Get quota value from description field.
        ldap_store = self.get_ldap_store()
        if not ldap_store:
            return False
        descriptions = ldap_store.get_user_attr(user, 'description')
        if not descriptions:
            return False
        quota_gb = [int(x[1:])
                    for x in descriptions
                    if x.startswith("v") and x[1:].isdigit()]
        if not quota_gb:
            return False
        quota_gb = max(quota_gb)
        return quota_gb * 1024 * 1024 * 1024

    def _getpwnam(self, user):
        assert isinstance(user, str)
        if PY3:
            return pwd.getpwnam(user)
        else:
            return pwd.getpwnam(encodefilename(user))

    def get_zfs_diskspace(self, user):
        """Get user disk quota and space."""
        assert isinstance(user, str)

        # Get ZFS pool name.
        if not self._zfs_pool:
            logger.warning('zfs pool name not provided. cannot get user [%s] quota', user)
            return None

        # Get user id (also check if local user).
        try:
            self._getpwnam(user)
        except KeyError:
            logger.info('user [%s] is not a real user. cannot get user quota', user)
            return None

        # Get value using zfs (as exact value).
        logger.debug('get user [%s] quota', user)
        p = subprocess.Popen(
            ['zfs', 'get', '-p', '-H', '-o', 'value', 'userused@%s,userquota@%s,used,available' % (user, user), self._zfs_pool],
            stdout=subprocess.PIPE)
        value = p.communicate()[0]
        values = value.splitlines()
        if len(values) != 4:
            raise RdiffError('fail to get user disk space: %s' % (value))
        userused, userquota, used, available = [int(x) for x in values]

        # If size is 0, the user doesn't have a quota. So use,
        if userquota:
            return {"size": userquota, "used": userused, "avail": userquota - userused}
        else:
            return {"size": used + available, "used": used, "avail": available}

    def _set_zfs_userquota(self, user, quota):
        """Update the user quota. Return True if quota update is successful."""
        assert user
        assert quota

        # Get ZFS pool name.
        if not self._zfs_pool:
            logger.warning('zfs pool name not provided. cannot set user [%s] quota', user)
            return False

        # Get user id (also check if local user).
        try:
            uid = self._getpwnam(user).pw_uid
        except KeyError:
            logger.info('user [%s] is not a real user. cannot set user quota', user)
            return False

        # Check if system user (for security)
        if uid < 1000:
            logger.info('user quota cannot be set for system user [%s]', user)
            return False

        logger.info('update user [%s] quota [%s]', user, quota)
        p = subprocess.Popen(
            ['zfs', 'set', 'userquota@%s=%s' % (user, quota), self._zfs_pool],
            stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = p.communicate()[0]
        if p.returncode != 0:
            logger.error(output)
            return False
        logger.debug(output)
        return True

    def _update_userquota(self, user, default_quota=5):
        """
        Get quota from LDAP and update the ZFS quota if required.
        """
        # Get user quota from LDAP server.
        quota = self.get_ldap_userquota(user)
        if not quota and not default_quota:
            logger.info('user [%s] quota not defined', user)
            return False
        quota = max(quota, default_quota * 1024 * 1024 * 1024)

        # Check if update required
        diskspace = self.get_zfs_diskspace(user)
        if not diskspace or quota == diskspace['size']:
            logger.info('user [%s] quota [%s] does not required update', user, quota)
            return True

        # Set Quota
        return self._set_zfs_userquota(user, quota)

    def user_added(self, user, password):
        """
        When added (manually or not). Try to get data from LDAP.
        """
        assert isinstance(user, str)

        # Check if LDAP is available.
        ldap_store = self.get_ldap_store()
        if not ldap_store:
            return

        # Get user home directory from LDAP
        try:
            home_dir = ldap_store.get_home_dir(user)
            if not home_dir:
                home_dir = os.path.join(self._basedir, user)
            logger.debug('update user [%s] root directory [%s]', user, home_dir)
            self.app.userdb.set_user_root(user, home_dir)
        except:
            logger.warning('fail to update user root directory [%s]', user, exc_info=1)

        # Get user email from LDAP
        try:
            email = ldap_store.get_email(user)
            if email:
                logger.debug('update user [%s] email [%s]', user, email)
                self.app.userdb.set_email(user, email)
        except:
            logger.warning('fail to update user email [%s]', user, exc_info=1)

        # Setup Filesystem
        if home_dir:
            self._create_user_root(user, home_dir)

    def user_attr_changed(self, user, attrs={}):
        """
        When email is updated, try to update the LDAP.
        """
        pass

    def user_logined(self, user, password):
        """
        Need to verify LDAP quota and update ZFS quota if required.
        """
        assert isinstance(user, str)
        self._update_userquota(user, default_quota=0)
