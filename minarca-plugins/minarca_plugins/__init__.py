#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca disk space rdiffweb plugin
#
# Copyright (C) 2018 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import unicode_literals

import logging
import os
import pwd
from rdiffweb.core import RdiffError
from rdiffweb.core.config import Option, IntOption
from rdiffweb.core.user import IUserChangeListener, IUserQuota, UserObject
import sys

from builtins import str
import cherrypy
from future.utils.surrogateescape import encodefilename

import requests

PY3 = sys.version_info[0] == 3

try:
    from urllib.parse import urljoin  # @UnresolvedImport @UnusedImport
except:
    from urlparse import urljoin  # @UnresolvedImport @UnusedImport @Reimport

# Define logger for this module
logger = logging.getLogger(__name__)


def _getpwnam(user):
    assert isinstance(user, str)
    if PY3:
        return pwd.getpwnam(user)
    else:
        return pwd.getpwnam(encodefilename(user))


class TimeoutHTTPAdapter(requests.adapters.HTTPAdapter):

    def send(self, *args, **kwargs):
        # Enforce a timeout value if not defined.
        kwargs['timeout'] = kwargs.get('timeout', None)
        return super(TimeoutHTTPAdapter, self).send(*args, **kwargs)


class MinarcaUserSetup(IUserChangeListener, IUserQuota):
    """
    This plugin provide feedback information to the users about the disk usage.
    Since we define quota, this plugin display the user's quota.
    """
    
    _quota_api_url = Option('MinarcaQuotaApiUrl', 'http://minarca:secret@localhost:8081/')
    _mode = IntOption('MinarcaUserSetupDirMode', 0o0700)
    _basedir = Option('MinarcaUserSetupBaseDir', default='/home')

    def __init__(self, app):
        self.app = app
        self.session = requests.Session()
        self.session.mount('https://', TimeoutHTTPAdapter(pool_connections=2, pool_maxsize=5))
        self.session.mount('http://', TimeoutHTTPAdapter(pool_connections=2, pool_maxsize=5))

    def get_disk_usage(self, userobj):
        """
        Return the user disk space.
        """
        assert isinstance(userobj, UserObject)
        
        # Get Quota from web service
        url = os.path.join(self._quota_api_url, 'quota', userobj.username)
        r = self.session.get(url, timeout=1)
        r.raise_for_status()
        diskspace = r.json()
        assert diskspace and isinstance(diskspace, dict) and 'avail' in diskspace and 'used' in diskspace and 'size' in diskspace
        return diskspace

    def get_disk_quota(self, userobj):
        """
        Get's user's disk quota.
        """
        return self.get_disk_usage(userobj)['size']

    def set_disk_quota(self, userobj, quota):
        """
        Sets the user's quota.
        """
        assert isinstance(userobj, UserObject)
        assert quota
        
        # Always update unless quota not define
        logger.info('set  user [%s] quota [%s]', userobj.username, quota)
        url = os.path.join(self._quota_api_url, 'quota', userobj.username)
        r = self.session.post(url, data={'size': quota}, timeout=1)
        r.raise_for_status()
        diskspace = r.json()
        assert diskspace and isinstance(diskspace, dict) and 'avail' in diskspace and 'used' in diskspace and 'size' in diskspace
        return diskspace
    
    def user_logined(self, userobj, attrs):
        """
        Need to verify LDAP quota and update ZFS quota if required.
        """
        assert isinstance(userobj, UserObject)
     
        # Get quota value from description field.
        quota = False
        descriptions = attrs and attrs.get('description')
        if descriptions:
            quota_gb = [
                int(x[1:]) for x in descriptions
                if x.startswith("v") and x[1:].isdigit()]
            if quota_gb:
                quota_gb = max(quota_gb)
                quota = quota_gb * 1024 * 1024 * 1024
        
        # If we found a quota value, use quota api to set it.
        logger.info('found user [%s] quota [%s] from attrs', userobj.username, quota)
        if quota:
            userobj.disk_quota = quota

    def user_added(self, userobj, attrs):
        """
        When added (manually or not). Try to get data from LDAP.
        """
        assert isinstance(userobj, UserObject)
        try:
            if attrs:
                self._update_user_profile(userobj, attrs)
        except:
            logger.warning('fail to update user profile [%s]', userobj.username, exc_info=1)

    def _update_user_profile(self, userobj, attrs):
        """
        Called to update the user email and home directory from LDAP info.
        """
        # Get user email from LDAP
        email = attrs.get('mail', None)
        if email:
            logger.debug('update user [%s] email [%s]', userobj.username, email[0])
            userobj.email = email[0]

        home_dir = attrs.get('homeDirectory', None)
        if not home_dir:
            home_dir = os.path.join(self._basedir, userobj.username)
        logger.debug('update user [%s] root directory [%s]', userobj.username, home_dir)
        userobj.user_root = home_dir
        
        # Get User / Group id
        try:
            pwd_user = _getpwnam(userobj.username)
            uid = pwd_user.pw_uid
            gid = pwd_user.pw_gid
        except KeyError:
            uid = -1
            gid = -1

        # Create folder if missing
        if not os.path.exists(userobj.user_root):
            logger.info('creating user [%s] root dir [%s]', userobj.username, userobj.user_root)
            os.makedirs(userobj.user_root, mode=self._mode)
            os.chown(userobj.user_root, uid, gid)

        if not os.path.isdir(userobj.user_root):
            logger.exception('fail to create user [%s] root dir [%s]', userobj.username, userobj.user_root)
            raise RdiffError(_("failed to setup user profile"))

        # Create ssh subfolder
        ssh_dir = os.path.join(userobj.user_root, '.ssh')
        if not os.path.exists(ssh_dir):
            os.makedirs(ssh_dir, mode=0o0700)
            os.chown(ssh_dir, uid, gid)
