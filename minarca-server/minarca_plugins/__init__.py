#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2019 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import unicode_literals

from builtins import str
from io import StringIO
from io import open
import logging
import os
import pwd
import stat
import sys
import urllib

import requests

import cherrypy
from rdiffweb.core import RdiffError, authorizedkeys
from rdiffweb.core.authorizedkeys import AuthorizedKey
from rdiffweb.core.config import Option, IntOption, BoolOption
from rdiffweb.core.user import IUserChangeListener, IUserQuota, UserObject
import pkg_resources

PY3 = sys.version_info[0] == 3

try:
    from urllib.parse import urlparse, urljoin  # @UnresolvedImport @UnusedImport
except:
    from urlparse import urljoin  # @UnresolvedImport @UnusedImport @Reimport
    from urlparse import urlparse  # @UnresolvedImport @UnusedImport @Reimport

# Define logger for this module
logger = logging.getLogger(__name__)


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
    _mode = IntOption('MinarcaUserSetupDirMode', 0o0770)
    _basedir = Option('MinarcaUserBaseDir', default='/backups/')
    _minarca_shell = Option('MinarcaShell', default='/opt/minarca/bin/minarca-shell')
    _auth_options = Option('MinarcaAuthOptions', default='no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty')
    _minarca_remotehost = Option('MinarcaRemoteHost')
    _minarca_identity = Option('MinarcaRemoteHostIdentity', default='/etc/ssh')
    _restrited_basedir = BoolOption('MinarcaRestrictedToBasedDir', default=True)

    def __init__(self, app):
        self.app = app
        self.app.root.api.minarca = self.get_minarca
        self.session = requests.Session()
        self.session.mount('https://', TimeoutHTTPAdapter(pool_connections=2, pool_maxsize=5))
        self.session.mount('http://', TimeoutHTTPAdapter(pool_connections=2, pool_maxsize=5))

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_minarca(self):
        
        # RemoteHost
        remotehost = self._minarca_remotehost
        if not remotehost:
            remotehost = urlparse(cherrypy.request.base).hostname
        
        # Identity known_hosts
        identity = ""
        files = [f for f in os.listdir(self._minarca_identity) if f.startswith('ssh_host') if f.endswith('.pub')]
        for fn in files:
            with open(os.path.join(self._minarca_identity, fn)) as fh:
                identity += remotehost + " " + fh.read()
        
        # Get remote host value from config or from URL
        return {
            "version": pkg_resources.get_distribution("minarca-server").version,
            "remotehost": remotehost,
            "identity": identity,
        }
        
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
        # TODO This is specific to Minarca Saas. We need to change this.
        # Get quota value from LDAP field.
        quota = False
        descriptions = attrs and attrs.get('description')
        if descriptions:
            quota_gb = [
                int(x[1:]) for x in descriptions
                if x.startswith(b"v") and x[1:].isdigit()]
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
            self._update_user_email(userobj, attrs)
        except:
            logger.warning('fail to update user [%s] email from LDAP', userobj.username, exc_info=1)
        try:
            self._update_user_root(userobj, attrs)
        except:
            logger.warning('fail to update user [%s] root', userobj.username, exc_info=1)

    def user_attr_changed(self, userobj, attrs={}):
        """
        Listen to users attributes change to update the minarca authorized_keys.
        """
        # Update minarca's authorized_keys when users update their ssh keys.
        if 'authorizedkeys' in attrs:
            # TODO schedule a background task to update the authorized_keys.
            self._update_authorized_keys()
            
        if 'user_root' in attrs:
            self._update_user_root(userobj, attrs)

    def user_deleted(self, username):
        """
        When user get dleted, update the authorized_key.
        """
        self._update_authorized_keys()

    def _update_user_email(self, userobj, attrs):
        """
        Called to update the user email and home directory from LDAP info.
        """
        # Get user email from LDAP
        mail = attrs and attrs.get('mail', None)
        if not mail:
            return
        # mail might be a list.
        if hasattr(mail, '__getitem__') and len(mail):
            mail = mail[0]
            
        if isinstance(mail, bytes):
            mail = mail.decode('utf-8')
            
        logger.info('update user [%s] email from LDAP [%s]', userobj.username, mail)
        userobj.email = mail

    def _update_user_root(self, userobj, attrs):
        """
        Called to update the user's home directory. Either to define it with
        default value or restrict it to base dir.
        """
        # Define default user_home if not provided
        user_root = userobj.user_root or os.path.join(self._basedir, userobj.username)
        # Normalise path to avoid relative path.
        user_root = os.path.abspath(user_root)
        # Verify if the user_root is inside base dir.
        if self._restrited_basedir and not user_root.startswith(self._basedir):
            logger.warn('restrict user [%s] root [%s] to base dir [%s]', userobj.username, user_root, self._basedir)
            user_root = os.path.join(self._basedir, userobj.username)
        # Persist the value if different then original
        if userobj.user_root != user_root:
            userobj.user_root = user_root
            
        # Create folder if inside our base dir and missing.
        if user_root.startswith(self._basedir) and not os.path.exists(user_root):
            logger.info('creating user [%s] root dir [%s]', userobj.username, user_root)
            os.mkdir(user_root)
            os.chmod(user_root, self._mode)

        if not os.path.isdir(user_root):
            logger.exception('fail to create user [%s] root dir [%s]', userobj.username, user_root)

    def _update_authorized_keys(self):
        """
        Used to update the authorized_keys of minarca user.
        """
        
        # Create ssh subfolder
        ssh_dir = os.path.join(self._basedir, '.ssh')
        if not os.path.exists(ssh_dir):
            logger.info("creating .ssh folder [%s]", ssh_dir)
            os.mkdir(ssh_dir, 0o700)
        
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
        for userobj in self.app.userdb.list():
            for key in userobj.authorizedkeys:
                
                if key.fingerprint in seen:
                    logger.warn("duplicates key %s, sshd will ignore it")
                else:
                    seen.add(key.fingerprint)
                    
                # Add option to the key
                options = """command="%s '%s' '%s'",%s""" % (self._minarca_shell, userobj.username, userobj.user_root, self._auth_options)
                key = AuthorizedKey(options=options, keytype=key.keytype, key=key.key, comment=key.comment)
                
                # Write the new key
                authorizedkeys.add(new_data, key)
        
        # Write the new file
        logger.info("updating authorized_keys file [%s]", filename)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_data.getvalue())
