#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import grp
from io import StringIO
from io import open
import logging
import os
import pwd
import stat
import subprocess
from sys import stderr
import sys
import urllib
from urllib.parse import urlparse, urljoin

import cherrypy
import pkg_resources
from rdiffweb.core import RdiffError, authorizedkeys
from rdiffweb.core.authorizedkeys import AuthorizedKey
from rdiffweb.core.config import Option, IntOption, BoolOption
from rdiffweb.core.quota import QuotaException, QuotaUnsupported, DefaultUserQuota, IUserQuota
from rdiffweb.core.store import IUserChangeListener, UserObject
import requests
from requests.exceptions import HTTPError

# Define logger for this module
logger = logging.getLogger(__name__)


def raise_for_status(r):
    """
    Raise exception if the http return an error.
    """

    http_error_msg = ''
    if isinstance(r.reason, bytes):
        # We attempt to decode utf-8 first because some servers
        # choose to localize their reason strings. If the string
        # isn't utf-8, we fall back to iso-8859-1 for all other
        # encodings. (See PR #3538)
        try:
            reason = r.reason.decode('utf-8')
        except UnicodeDecodeError:
            reason = r.reason.decode('iso-8859-1')
    else:
        reason = r.reason

    if 400 <= r.status_code < 500:
        http_error_msg = u'%s Client Error: %s for url: %s' % (r.status_code, reason, r.text)

    elif 500 <= r.status_code < 600:
        http_error_msg = u'%s Server Error: %s for url: %s' % (r.status_code, reason, r.text)

    if http_error_msg:
        raise HTTPError(http_error_msg, response=self)


class TimeoutHTTPAdapter(requests.adapters.HTTPAdapter):

    def send(self, *args, **kwargs):
        # Enforce a timeout value if not defined.
        kwargs['timeout'] = kwargs.get('timeout', None)
        return super(TimeoutHTTPAdapter, self).send(*args, **kwargs)


class MinarcaUserSetup(IUserChangeListener):
    """
    This plugin provide feedback information to the users about the disk usage.
    Since we define quota, this plugin display the user's quota.
    """

    _mode = IntOption('MinarcaUserDirMode', 0o0770)
    _owner = Option('MinarcaUserDirOwner', 'minarca')
    _group = Option('MinarcaUserDirGroup', 'minarca')
    _basedir = Option('MinarcaUserBaseDir', default='/backups/')
    _minarca_shell = Option('MinarcaShell', default='/opt/minarca-server/bin/minarca-shell')
    _auth_options = Option('MinarcaAuthOptions', default='no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty')
    _minarca_remotehost = Option('MinarcaRemoteHost')
    _minarca_identity = Option('MinarcaRemoteHostIdentity', default='/etc/ssh')
    _restrited_basedir = BoolOption('MinarcaRestrictedToBasedDir', default=True)
    _redirect_help = Option('MinarcaHelpURL', default='https://www.ikus-soft.com/en/support/#form')

    def __init__(self, app):
        self.app = app
        self.app.root.api.minarca = self.get_minarca
        self.app.root.help = self.get_help
        self.app.cfg['footername'] = 'Minarca'
        self.app.cfg['footerurl'] = 'https://www.ikus-soft.com/en/minarca/'
        # On startup Upgrade the authorized_keys in case the configuration changed.
        try:
            self._update_authorized_keys()
        except:
            logger.error("fail to update authorized_keys files on startup", exc_info=1)

    @cherrypy.expose
    @cherrypy.config(**{'tools.authform.on': False, 'tools.i18n.on': False, 'tools.authbasic.on': False, 'tools.sessions.on': False, 'error_page.default': False})
    def get_help(self):
        raise cherrypy.HTTPRedirect(self._redirect_help)

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
                if ':' in remotehost:
                    hostname, port = remotehost.split(':', 1)
                    identity += "[" + hostname + "]:" + port + " " + fh.read()
                else:
                    identity += remotehost + " " + fh.read()

        # Get remote host value from config or from URL
        return {
            "version": pkg_resources.get_distribution("minarca-server").version,
            "remotehost": remotehost,
            "identity": identity,
        }

    def user_logined(self, userobj, attrs):
        """
        Need to verify LDAP quota and update ZFS quota if required.
        """
        pass

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
        if 'user_root' in attrs:
            self._update_user_root(userobj, attrs)

        # Update minarca's authorized_keys when users update their ssh keys.
        if 'authorizedkeys' in attrs or 'user_root' in attrs:
            # TODO schedule a background task to update the authorized_keys.
            try:
                self._update_authorized_keys()
            except:
                logger.error("fail to update authorized_keys files on user_attr_changed", exc_info=1)

    def user_deleted(self, username):
        """
        When user get deleted, update the authorized_key.
        """
        try:
            self._update_authorized_keys()
        except:
            logger.error("fail to update authorized_keys files on user_deleted", exc_info=1)

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
            try:
                os.mkdir(user_root)
                # Change mode
                os.chmod(user_root, self._mode)
                # Change owner
                os.chown(user_root, pwd.getpwnam(self._owner).pw_uid, grp.getgrnam(self._group).gr_gid)
            except:
                logger.warn('fail to create user [%s] root dir [%s]', userobj.username, user_root)

    def _update_authorized_keys(self):
        """
        Used to update the authorized_keys of minarca user.
        """

        # Create ssh subfolder
        ssh_dir = os.path.join(self._basedir, '.ssh')
        if not os.path.exists(ssh_dir):
            logger.info("creating .ssh folder [%s]", ssh_dir)
            os.mkdir(ssh_dir, 0o700)

        os.chown(ssh_dir, pwd.getpwnam(self._owner).pw_uid, grp.getgrnam(self._group).gr_gid)

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
        for userobj in self.app.store.users():
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


class MinarcaQuota(IUserQuota):

    _quota_api_url = Option('MinarcaQuotaApiUrl', '')

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
        # Fallback to default user quota if quota url is not provided.
        if not self._quota_api_url:
            return DefaultUserQuota.get_disk_usage(self, userobj)
        # Get Quota from web service
        url = os.path.join(self._quota_api_url, 'quota', str(userobj.userid))
        try:
            r = self.session.get(url, timeout=1)
            r.raise_for_status()
            diskspace = r.json()
            return diskspace['used']
        except:
            logger.warn('fail to get user quota [%s]', userobj.username, exc_info=1)
            return 0

    def get_disk_quota(self, userobj):
        """
        Get's user's disk quota.
        """
        # Fallback to default user quota if quota url is not provided.
        if not self._quota_api_url:
            return DefaultUserQuota.get_disk_usage(self, userobj)
        # Get Quota from web service
        url = os.path.join(self._quota_api_url, 'quota', str(userobj.userid))
        try:
            r = self.session.get(url, timeout=1)
            r.raise_for_status()
            diskspace = r.json()
            return diskspace['size']
        except:
            logger.warn('fail to get user quota [%s]', userobj.username, exc_info=1)
            return 0

    def set_disk_quota(self, userobj, quota):
        """
        Sets the user's quota.
        """
        # Fallback to default user quota if quota url is not provided.
        if not self._quota_api_url:
            return DefaultUserQuota.get_disk_usage(self, userobj)

        # Always update unless quota not define
        try:
            logger.info('set user [%s] quota [%s]', userobj.username, quota)
            url = os.path.join(self._quota_api_url, 'quota', str(userobj.userid))
            r = self.session.post(url, data={'size': quota}, timeout=1)
            raise_for_status(r)
        except Exception as e:
            logger.warn("fail to update user root quota", exc_info=1)
            raise QuotaException(str(e))

        # Update user root attribute
        try:
            # Add +P attribute to user's home directory
            subprocess.check_output(["/usr/bin/chattr", "-R", "+P", userobj.user_root], stderr=subprocess.STDOUT)
            # Force project id on directory
            subprocess.check_output(["/usr/bin/chattr", "-R", "-p", str(userobj.userid), userobj.user_root], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise QuotaException(e.output)
        except Exception as e:
            raise QuotaException(str(e))
