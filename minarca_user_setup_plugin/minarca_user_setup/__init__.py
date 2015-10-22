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
import logging
import os
import subprocess

from rdiffweb.rdw_plugin import IRdiffwebPlugin, IUserChangeListener
from rdiffweb.core import RdiffError


logger = logging.getLogger(__name__)


class MinarcaUserSetup(IUserChangeListener):

    @property
    def _mode(self):
        return self.app.cfg.get_config_int('MinarcaUserSetupDirMode', 0700)

    @property
    def _basedir(self):
        return self.app.cfg.get_config('MinarcaUserSetupBaseDir', '/home')

    def _create_user_root(self, user, user_root):
        """Create and configure user home directory"""
        # Create folder if missing
        if not os.path.exists(user_root):
            logger.info('creating user [%s] root dir [%s]', user, user_root)
            os.makedirs(user_root, mode=self._mode)
        if not os.path.isdir(user_root):
            raise RdiffError(_('fail to create user [%s] root dir [%s]', user, user_root))

        # Create ssh subfolder
        ssh_dir = os.path.join(user_root, '.ssh')
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, mode=0700)

        # Define default user quota
        if distutils.spawn.find_executable('zfs'):
            subprocess.call(['zfs', 'set', 'userquota@%s=%s' % (user, '50G'), 'tank'])

    def get_ldap_store(self):
        """get reference to ldap_store"""
        plugin = self.app.plugins.get_plugin_by_name('Ldap')
        if plugin:
            return plugin.plugin_object
        return None

    def user_added(self, user, password):
        """
        When added (manually or not). Try to get data from LDAP.
        """
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
