#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca Quota API
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
"""
Created on Mar 7, 2018

@author: Patrik Dufresne <patrik@ikus-soft.com>
"""

import logging
import logging.handlers
import sys

import cherrypy
import configargparse

from minarca_quota_api.zfs_quota import get_quota, is_project_quota_enabled, set_quota

try:
    import pkg_resources

    __version__ = pkg_resources.get_distribution("minarca-quota-api").version
except Exception:
    __version__ = 'DEV'


logger = logging.getLogger(__name__)


def _parse_args(args):
    parser = configargparse.ArgParser(
        prog='minarca-quota-api',
        description='Web server to manage user quota.',
        default_config_files=['/etc/minarca/minarca-quota-api.conf', '/etc/minarca/minarca-quota-api.conf.d/*.conf'],
        add_env_var_help=True,
        auto_env_var_prefix='MINARCA_QUOTA_',
    )
    parser.add('-f', '--config', is_config_file=True, help='configuration file path')
    parser.add('-v', '--version', action='version', version='minarca-quota-api ' + __version__)
    parser.add('--serverhost', metavar='IP', help='Define the IP address to listen to.', default='127.0.0.1')
    parser.add('--serverport', metavar='PORT', help='Define the port to listen to.', default='8081', type=int)
    parser.add('--logfile', metavar='FILE', help='Define the location of the log file.', default='')
    parser.add('--logaccessfile', metavar='FILE', help='Define the location of the access log file.', default='')
    parser.add(
        '--pool',
        '--zfs-pool',
        metavar='POOL',
        help="Define the ZFS pool to be updated with user's quota.",
        default='rpool/minarca',
    )
    parser.add('--secret', metavar='SECRET', help="Secret to be used to authenticate to the service.", default='secret')
    return parser.parse_args(args)


def _error_page(**kwargs):
    """
    Custom error page to return plain text error message.
    """
    cherrypy.response.headers['Content-Type'] = 'text/plain'
    return kwargs.get('message')


def _setup_logging(log_file, log_access_file, level):
    """
    Configure the logging system for cherrypy.
    """
    assert isinstance(logging.getLevelName(level), int)

    def remove_cherrypy_date(record):
        """Remove the leading date for cherrypy error."""
        if record.name.startswith('cherrypy.error'):
            record.msg = record.msg[23:].strip()
        return True

    def add_ip(record):
        """Add request IP to record."""
        if hasattr(cherrypy, 'serving'):
            request = cherrypy.serving.request
            remote = request.remote
            record.ip = remote.name or remote.ip
            # If the request was forwarded by a reverse proxy
            if 'X-Forwarded-For' in request.headers:
                record.ip = request.headers['X-Forwarded-For']
        return True

    def add_username(record):
        """Add current username to record."""
        record.user = cherrypy.request and cherrypy.request.login or "anonymous"
        return True

    cherrypy.config.update({'log.screen': False, 'log.access_file': '', 'log.error_file': ''})
    cherrypy.engine.unsubscribe('graceful', cherrypy.log.reopen_files)

    # Configure root logger
    logger = logging.getLogger('')
    logger.level = logging.getLevelName(level)
    if log_file:
        print("continue logging to %s" % log_file)
        default_handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=10485760, backupCount=20)
    else:
        default_handler = logging.StreamHandler(sys.stdout)
    default_handler.addFilter(remove_cherrypy_date)
    default_handler.addFilter(add_ip)
    default_handler.addFilter(add_username)
    default_handler.setFormatter(
        logging.Formatter("[%(asctime)s][%(levelname)-7s][%(ip)s][%(user)s][%(threadName)s][%(name)s] %(message)s")
    )
    logger.addHandler(default_handler)

    # Configure cherrypy access logger
    cherrypy_access = logging.getLogger('cherrypy.access')
    cherrypy_access.propagate = False
    if log_access_file:
        handler = logging.handlers.RotatingFileHandler(log_access_file, maxBytes=10485760, backupCount=20)
        cherrypy_access.addHandler(handler)

    # Configure cherrypy error logger
    cherrypy_error = logging.getLogger('cherrypy.error')
    cherrypy_error.propagate = False
    cherrypy_error.addHandler(default_handler)


class Root(object):
    def __init__(self, pool):
        self.pool = pool

    @cherrypy.expose
    def index(self):
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return 'Minarca Quota API'

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def quota(self, user, size=None):
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        # Validate userid
        try:
            user = int(user)
        except ValueError:
            raise cherrypy.HTTPError(400, 'invalid uid: ' + user)
        # Validate size
        try:
            if size:
                size = int(size)
        except ValueError:
            raise cherrypy.HTTPError(400, 'invalid size: ' + size)

        if cherrypy.request.method in ['PUT', 'POST']:
            logger.info('update user [%s] quota [%s]' % (user, size))
            set_quota(projectid=user, pool=self.pool, quota=size)

        logger.info('get user [%s] quota' % user)
        return get_quota(projectid=user, pool=self.pool)


def run(args=None):
    args = _parse_args(sys.argv[1:] if args is None else args)

    _setup_logging(log_file=args.logfile, log_access_file=args.logaccessfile, level='INFO')

    # Configure authentication.
    checkpassword = cherrypy.lib.auth_basic.checkpassword_dict({'minarca': args.secret})  # @UndefinedVariable
    basic_auth = {
        'tools.auth_basic.on': True,
        'tools.auth_basic.realm': 'earth',
        'tools.auth_basic.checkpassword': checkpassword,
        'tools.auth_basic.accept_charset': 'UTF-8',
    }
    app_config = {'/': basic_auth}

    # configure web server
    cherrypy.config.update(
        {
            'server.socket_host': args.serverhost,
            'server.socket_port': args.serverport,
            'error_page.default': _error_page,
            'environment': 'production',
        }
    )

    # Check if ZFS project quota is enabled.
    if not is_project_quota_enabled(pool=args.pool):
        cherrypy.log(
            "ZFS project quota is not enabled for the pool %s. pool and or dataset must be upgraded" % args.pool
        )

    # start app
    cherrypy.quickstart(Root(pool=args.pool), '/', config=app_config)


if __name__ == '__main__':  # Script executed directly?
    run()
