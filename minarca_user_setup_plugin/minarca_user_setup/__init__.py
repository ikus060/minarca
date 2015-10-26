#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca disk space rdiffweb plugin
#
# Copyright (C) 2015 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import unicode_literals

import pwd
import distutils.spawn
import logging
import os
import subprocess

from rdiffweb.rdw_plugin import IRdiffwebPlugin, IUserChangeListener
from rdiffweb.core import RdiffError
from rdiffweb.rdw_helpers import encode_s
from subprocess import Popen


logger = logging.getLogger(__name__)


class MinarcaUserSetup(IUserChangeListener):

    @property
    def _mode(self):
        return self.app.cfg.get_config_int('MinarcaUserSetupDirMode', 0700)

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
            pwd_user = pwd.getpwnam(encode_s(user))
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
            os.makedirs(ssh_dir, mode=0700)
            os.chown(ssh_dir, uid, gid)

        # Get user quota from LDAP server.
        quota = self.get_ldap_userquota(user)
        if not quota:
            logger.info('user [%s] quota not defined', user)
        quota = max(quota, 5 * 1024 * 1024 * 1024)

        # Set Quota
        self._set_zfs_userquota(user, quota)

    def get_ldap_store(self):
        """get reference to ldap_store"""
        plugin = self.app.plugins.get_plugin_by_name('Ldap')
        if plugin:
            return plugin.plugin_object
        return None

    def get_ldap_userquota(self, user):
        """Get userquota from LDAP database."""

        # Get quota value from description field.
        ldap_store = self.get_ldap_store()
        if not ldap_store:
            return False
        descriptions = ldap_store.get_user_attr(user, 'description')
        quota_gb = [int(x[1:])
                    for x in descriptions
                    if x.startswith("v") and x[1:].isdigit()]
        if not quota_gb:
            return False
        quota_gb = max(quota_gb)
        return quota_gb * 1024 * 1024 * 1024

    def get_userquota(self, user):
        """Get filesystem user quota."""
        return self._get_zfs_userquota(user)

    def _get_zfs_userquota(self, user):
        """Get userquota from zfs."""

        # Get ZFS pool name.
        if not self._zfs_pool:
            logger.warn('zfs pool name not provided. cannot set user [%s] quota', user)
            return False

        # Check if zfs is available
        if not distutils.spawn.find_executable('zfs'):
            logger.warn('zfs executable not found to setup user [%s] quota', user)
            return False

        # Get value using zfs (as exact value).
        logger.debug('get user [%s] quota', user)
        p = Popen(['zfs', 'get', '-p', '-H', '-o', 'value', 'userquota@%s' % (user,), self._zfs_pool], stdout=subprocess.PIPE)
        value = p.communicate()[0]
        if not value.isdigit():
            return False
        return value

    def _set_zfs_userquota(self, user, quota):
        """Update the user quota"""
        assert user
        assert quota

        # Get ZFS pool name.
        if not self._zfs_pool:
            logger.warn('zfs pool name not provided. cannot set user [%s] quota', user)
            return

        # Get user id (also check if local user).
        try:
            uid = pwd.getpwnam(encode_s(user)).pw_uid
        except KeyError:
            logger.info('user [%s] is not a real user. cannot set user quota', user)
            return

        # Check if system user (for security)
        if uid < 1000:
            logger.info('user quota cannot be set for system user [%s]', user)
            return

        # Check if zfs is available
        if not distutils.spawn.find_executable('zfs'):
            logger.warn('zfs executable not found to setup user [%s] quota', user)
            return

        logger.info('update user [%s] quota [%s]', user, quota)
        p = subprocess.Popen(
            ['zfs', 'set', 'userquota@%s=%s' % (user, quota), self._zfs_pool],
            stdin=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = p.communicate()[0]
        logger.debug(output)

    def user_added(self, user, password):
        """
        When added (manually or not). Try to get data from LDAP.
        """
        assert isinstance(user, unicode)
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
            logger.warn('fail to update user root directory [%s]', user, exc_info=1)

        # Get user email from LDAP
        try:
            email = ldap_store.get_email(user)
            if email:
                logger.debug('update user [%s] email [%s]', user, email)
                self.app.userdb.set_email(user, email)
        except:
            logger.warn('fail to update user email [%s]', user, exc_info=1)

        # Setup Filesystem
        if home_dir:
            self._create_user_root(user, home_dir)

    def user_attr_changed(self, user, attrs={}):
        """
        When email is updated, try to update the LDAP.
        """
