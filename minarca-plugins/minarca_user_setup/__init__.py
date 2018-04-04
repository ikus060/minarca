#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca disk space rdiffweb plugin
#
# Copyright (C) 2018 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import unicode_literals

from builtins import str
import distutils.spawn
from future.utils.surrogateescape import encodefilename
import logging
import os
import pwd
from subprocess import Popen
import subprocess
import sys

from rdiffweb.core import RdiffError
from rdiffweb.rdw_plugin import IRdiffwebPlugin, IUserChangeListener
from rdiffweb import rdw_config
import requests
import cherrypy

logger = logging.getLogger(__name__)

PY3 = sys.version_info[0] == 3


def _getpwnam(user):
    assert isinstance(user, str)
    if PY3:
        return pwd.getpwnam(user)
    else:
        return pwd.getpwnam(encodefilename(user))


class MinarcaUserSetup(IUserChangeListener):

    _mode = rdw_config.IntOption('MinarcaUserSetupDirMode', 0o0700)
    _basedir = rdw_config.Option('MinarcaUserSetupBaseDir', default='/home')

    def user_added(self, user, password):
        """
        When added (manually or not). Try to get data from LDAP.
        """
        assert isinstance(user, str)
        try:
            self._update_user_profile(user)
        except:
            logger.warning('fail to update user profile [%s]', user, exc_info=1)

    def user_attr_changed(self, user, attrs={}):
        pass

    def user_logined(self, user, password):
        pass

    def _create_user_root(self, user, user_root):
        """Create and configure user home directory"""

        # Get User / Group id
        try:
            pwd_user = _getpwnam(user)
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
            logger.exception('fail to create user [%s] root dir [%s]', user, user_root)
            raise RdiffError(_("failed to setup user profile"))

        # Create ssh subfolder
        ssh_dir = os.path.join(user_root, '.ssh')
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, mode=0o0700)
            os.chown(ssh_dir, uid, gid)

    def get_ldap_store(self):
        """get reference to ldap_store"""
        plugin = self.app.plugins.get_plugin_by_name('LdapPasswordStore')
        assert plugin
        return plugin

    def _update_user_profile(self, user):
        """
        Called to update the user email and home directory from LDAP info.
        """
        # Get user email from LDAP
        home_dir = None
        try:
            ldap_store = self.get_ldap_store()
            email = ldap_store.get_email(user)
            if email:
                logger.debug('update user [%s] email [%s]', user, email)
                self.app.userdb.get_user(user).set_attr('email', email, notify=False)

            home_dir = ldap_store.get_home_dir(user)
            if not home_dir:
                home_dir = os.path.join(self._basedir, user)
            logger.debug('update user [%s] root directory [%s]', user, home_dir)
            self.app.userdb.get_user(user).user_root = home_dir
        finally:
            # Setup Filesystem
            if home_dir:
                self._create_user_root(user, home_dir)
