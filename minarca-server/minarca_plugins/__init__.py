#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import argparse
import grp
from io import StringIO
from io import open
import logging
import os
import pwd
import stat
import subprocess
from urllib.parse import urlparse

import cherrypy
import pkg_resources
import rdiffweb
from rdiffweb.core import authorizedkeys
from rdiffweb.core.authorizedkeys import AuthorizedKey
from rdiffweb.core.config import Option
from rdiffweb.core.quota import QuotaException, DefaultUserQuota
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
        http_error_msg = u'%s Client Error: %s for url: %s' % (
            r.status_code, reason, r.text)

    elif 500 <= r.status_code < 600:
        http_error_msg = u'%s Server Error: %s for url: %s' % (
            r.status_code, reason, r.text)

    if http_error_msg:
        raise HTTPError(http_error_msg, response=r)


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

    _logfile = Option('log_file')
    _logaccessfile = Option('log_access_file')
    _mode = Option('minarca_user_dir_mode')
    _owner = Option('minarca_user_dir_owner')
    _group = Option('minarca_user_dir_group')
    _basedir = Option('minarca_user_base_dir')
    _minarca_shell = Option('minarca_shell')
    _auth_options = Option('minarca_auth_options')
    _minarca_remotehost = Option('minarca_remote_host')
    _minarca_identity = Option('minarca_remote_host_identity')
    _restrited_basedir = Option('minarca_restricted_to_based_dir')
    _redirect_help = Option('minarca_help_url')

    @classmethod
    def add_arguments(cls, parser):
        parser.add(
            '--minarca-user-dir-mode', '--minarcauserdirmode',
            metavar='MODE',
            help=argparse.SUPPRESS,
            type=int,
            default=0o0770)

        parser.add(
            '--minarca-user-dir-owner', '--minarcauserdirowner',
            metavar='OWNER',
            help=argparse.SUPPRESS,
            default='minarca')

        parser.add(
            '--minarca-user-dir-group', '--minarcauserdirgroup',
            metavar='GROUP',
            help=argparse.SUPPRESS,
            default='minarca')

        parser.add(
            '--minarca-user-base-dir', '--minarcauserbasedir', '--minarcausersetupbasedir',
            metavar='FOLDER',
            help="""base directory where all the backup should reside. Any
                user_root outside this repository will be refused.""",
            default='/backups/')

        parser.add(
            '--minarca-restricted-to-based-dir', '--minarcarestrictedtobaseddir',
            action='store_true',
            help=argparse.SUPPRESS,
            default=True)

        parser.add(
            '--minarca-shell', '--minarcashell',
            metavar='FILE',
            help="""location of minarca-shell to be used to handle SSH
                connection. This is used to configure `authorized_keys` to
                restrict SSH command line to be executed""",
            default='/opt/minarca-server/bin/minarca-shell')

        parser.add(
            '--minarca-auth-options', '--minarcaauthoptions',
            metavar='OPTIONS',
            help="""authentication option to be passed to `authorized_keys`.
                This is used to limit the user's permission on the SSH Server,
                effectively disabling X11 forwarding, port forwarding and PTY.""",
            default='no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty')

        parser.add(
            '--minarca-remote-host', '--minarcaremotehost',
            metavar='HOST:PORT',
            help="""the remote SSH identity. This value is queried by Minarca
                Client to link and back up to the server. If not provided, the
                HTTP URL is used as a base. You may need to change this value
                if the SSH server is accessible using a different IP address
                or if not running on port 22. e.g.: ssh.example.com:2222""")

        parser.add(
            '--minarca-remote-host-identity', '--minarcaremotehostidentity',
            metavar='FOLDER',
            help="""location of SSH server identity. This value is queried by
                Minarca Client to authenticate the server. You may need to
                change this value if SSH service and the Web service are not
                running on the same server.""",
            default="/etc/ssh")

        parser.add(
            '--minarca-help-url', '--minarcahelpurl',
            metavar='URL',
            help="""custom URL where to redirect user clicking on help button""",
            default="https://www.ikus-soft.com/en/support/#form")

        parser.add(
            '--minarca-rdiff-backup-extra-args', '--rdiffbackup-args',
            metavar='ARGS',
            help="""list of extra argumenst to be pass to rdiff-backup server. e.g.: --no-compression""")

        # Replace default config file
        parser._default_config_files = [
            '/etc/minarca/minarca-server.conf', '/etc/minarca/conf.d/*.conf']

        # Override a couple of arguments with Minarca.
        parser.set_defaults(
            database_uri='/etc/minarca/rdw.db',
            default_theme='blue',
            favicon=pkg_resources.resource_filename(
                __name__, 'minarca.ico'),  # @UndefinedVariable
            footer_name='Minarca',
            footer_url='https://www.ikus-soft.com/en/minarca/',
            header_name='Minarca',
            header_logo=pkg_resources.resource_filename(
                __name__, 'minarca_22.png'),  # @UndefinedVariable
            log_access_file='/var/log/minarca/access.log',
            log_file='/var/log/minarca/server.log',
            welcome_msg={
                '': 'A <b>free and open-source</b> backup software providing end-to-end integration to put you in control of your backup strategy.<br/><br/><a href="https://www.ikus-soft.com/en/minarca/">website</a> • <a href="https://www.ikus-soft.com/en/minarca/doc/">docs</a> • <a href="https://groups.google.com/d/forum/minarca">community</a>',
                'fr': 'Un logiciel de sauvegarde <b>gratuit et à code source ouvert</b> fournissant une intégration bout en bout pour vous permettre de contrôler votre stratégie de sauvegarde.<br/><br/> <a href="https://www.ikus-soft.com/fr/minarca/">site web</a> • <a href="https://www.ikus-soft.com/fr/minarca/doc/">documentations</a> • <a href="https://groups.google.com/d/forum/minarca">communauté</a>',
            }
        )

    def __init__(self, app):
        self.app = app
        self.app.root.api.minarca = self.get_minarca
        self.app.root.help = self.get_help

        # Monkey patch admin view to show minarca-shell.
        self._orig_get_log_files = self.app.root.admin._get_log_files
        self.app.root.admin._get_log_files = self._get_log_files

        # On startup Upgrade the authorized_keys in case the configuration
        # changed.
        try:
            self._update_authorized_keys()
        except Exception:
            logger.error(
                "fail to update authorized_keys files on startup", exc_info=1)

    @cherrypy.expose
    @cherrypy.config(**{'tools.auth_form.on': False, 'tools.i18n.on': False, 'tools.auth_basic.on': False, 'tools.sessions.on': False, 'error_page.default': False})
    def get_help(self):
        raise cherrypy.HTTPRedirect(self._redirect_help)

    def _get_log_files(self):
        """Patched version of _get_log_files"""
        minarca_shell_logfile = os.path.join(os.path.dirname(
            self._logfile or '/var/log/minarca/server.log'), 'shell.log')
        logfiles = self._orig_get_log_files()
        logfiles.append(minarca_shell_logfile)
        return logfiles

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_minarca(self):

        # RemoteHost
        remotehost = self._minarca_remotehost
        if not remotehost:
            remotehost = urlparse(cherrypy.request.base).hostname

        # Identity known_hosts
        identity = ""
        files = [f for f in os.listdir(self._minarca_identity) if f.startswith(
            'ssh_host') if f.endswith('.pub')]
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
        pass

    def user_added(self, userobj, attrs):
        """
        When added (manually or not). Update user's attributes.
        """
        assert isinstance(userobj, UserObject)
        try:
            self._update_user_root(userobj, attrs)
        except Exception:
            logger.warning(
                'fail to update user [%s] root', userobj.username, exc_info=1)

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
            except Exception:
                logger.error(
                    "fail to update authorized_keys files on user_attr_changed", exc_info=1)

    def user_deleted(self, username):
        """
        When user get deleted, update the authorized_key.
        """
        try:
            self._update_authorized_keys()
        except Exception:
            logger.error(
                "fail to update authorized_keys files on user_deleted", exc_info=1)

    def _update_user_root(self, userobj, attrs):
        """
        Called to update the user's home directory. Either to define it with
        default value or restrict it to base dir.
        """
        # Define default user_home if not provided
        user_root = userobj.user_root or os.path.join(
            self._basedir, userobj.username)
        # Normalise path to avoid relative path.
        user_root = os.path.abspath(user_root)
        # Verify if the user_root is inside base dir.
        if self._restrited_basedir and not user_root.startswith(self._basedir):
            logger.warning(
                'restrict user [%s] root [%s] to base dir [%s]', userobj.username, user_root, self._basedir)
            user_root = os.path.join(self._basedir, userobj.username)
        # Persist the value if different then original
        if userobj.user_root != user_root:
            userobj.user_root = user_root

        # Create folder if inside our base dir and missing.
        if user_root.startswith(self._basedir) and not os.path.exists(user_root):
            logger.info(
                'creating user [%s] root dir [%s]', userobj.username, user_root)
            try:
                os.mkdir(user_root)
                # Change mode
                os.chmod(user_root, self._mode)
                # Change owner
                os.chown(user_root, pwd.getpwnam(self._owner).pw_uid,
                         grp.getgrnam(self._group).gr_gid)
            except Exception:
                logger.warning(
                    'fail to create user [%s] root dir [%s]', userobj.username, user_root)

    def _update_authorized_keys(self):
        """
        Used to update the authorized_keys of minarca user.
        """

        # Create ssh subfolder
        ssh_dir = os.path.join(self._basedir, '.ssh')
        if not os.path.exists(ssh_dir):
            logger.info("creating .ssh folder [%s]", ssh_dir)
            os.mkdir(ssh_dir, 0o700)

        os.chown(ssh_dir, pwd.getpwnam(self._owner).pw_uid,
                 grp.getgrnam(self._group).gr_gid)

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
                    logger.warning("duplicates key %s, sshd will ignore it")
                else:
                    seen.add(key.fingerprint)

                # Add option to the key

                options = """command="export MINARCA_USERNAME='{username}' MINARCA_USER_ROOT='{user_root}';{minarca_shell}",{auth_options}""".format(
                    minarca_shell=self._minarca_shell,
                    username=userobj.username,
                    user_root=userobj.user_root,
                    auth_options=self._auth_options)

                key = AuthorizedKey(
                    options=options, keytype=key.keytype, key=key.key, comment=key.comment)

                # Write the new key
                authorizedkeys.add(new_data, key)

        # Write the new file
        logger.info("updating authorized_keys file [%s]", filename)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_data.getvalue())


class MinarcaQuota(DefaultUserQuota):

    _logfile = Option('log_file')
    _quota_api_url = Option('minarca_quota_api_url')

    @classmethod
    def add_arguments(cls, parser):
        parser.add(
            '--minarca-quota-api-url', '--minarcaquotaapiurl',
            metavar='URL',
            help="url to minarca-quota-api server")

    def __init__(self, app):
        self.app = app
        self.session = requests.Session()
        self.session.mount(
            'https://', TimeoutHTTPAdapter(pool_connections=2, pool_maxsize=5))
        self.session.mount(
            'http://', TimeoutHTTPAdapter(pool_connections=2, pool_maxsize=5))

        # Monkey patch admin view to show quota.log.
        if self._quota_api_url:
            self._orig_get_log_files = self.app.root.admin._get_log_files
            self.app.root.admin._get_log_files = self._get_log_files

    def get_disk_usage(self, userobj):
        """
        Return the user disk space.
        """
        assert isinstance(userobj, UserObject)
        # Fallback to default user quota if quota url is not provided.
        if not self._quota_api_url:
            return super().get_disk_usage(userobj)
        # Get Quota from web service
        url = os.path.join(self._quota_api_url, 'quota', str(userobj.userid))
        try:
            r = self.session.get(url, timeout=1)
            r.raise_for_status()
            diskspace = r.json()
            return diskspace['used']
        except Exception:
            logger.warning(
                'fail to get user quota [%s]', userobj.username, exc_info=1)
            return 0

    def get_disk_quota(self, userobj):
        """
        Get's user's disk quota.
        """
        # Fallback to default user quota if quota url is not provided.
        if not self._quota_api_url:
            return super().get_disk_quota(userobj)
        # Get Quota from web service
        url = os.path.join(self._quota_api_url, 'quota', str(userobj.userid))
        try:
            r = self.session.get(url, timeout=1)
            r.raise_for_status()
            diskspace = r.json()
            return diskspace['size']
        except Exception:
            logger.warning(
                'fail to get user quota [%s]', userobj.username, exc_info=1)
            return 0

    def _get_log_files(self):
        """Patched version of _get_log_files"""
        logfiles = self._orig_get_log_files()
        minarca_quota_logfile = os.path.join(os.path.dirname(
            self._logfile or '/var/log/minarca/server.log'), 'quota-api.log')
        if os.path.isfile(minarca_quota_logfile):
            logfiles.append(minarca_quota_logfile)
        return logfiles

    def set_disk_quota(self, userobj, quota):
        """
        Sets the user's quota.
        """
        # Fallback to default user quota if quota url is not provided.
        if not self._quota_api_url:
            super().set_disk_quota(userobj, quota)

        # Always update unless quota not define
        try:
            logger.info('set user [%s] quota [%s]', userobj.username, quota)
            url = os.path.join(self._quota_api_url,
                               'quota', str(userobj.userid))
            r = self.session.post(url, data={'size': quota}, timeout=1)
            raise_for_status(r)
        except Exception as e:
            logger.warning("fail to update user root quota", exc_info=1)
            raise QuotaException(str(e))

        # Update user root attribute
        try:
            # Add +P attribute to user's home directory
            subprocess.check_output(
                ["/usr/bin/chattr", "-R", "+P", userobj.user_root], stderr=subprocess.STDOUT)
            # Force project id on directory
            subprocess.check_output(["/usr/bin/chattr", "-R", "-p", str(
                userobj.userid), userobj.user_root], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise QuotaException(e.output)
        except Exception as e:
            raise QuotaException(str(e))


def main(args=None):
    rdiffweb.main.main(args)
