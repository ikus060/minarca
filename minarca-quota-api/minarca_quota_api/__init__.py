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

@author: Patrik Dufresne
"""

import logging
import os
import pwd
import subprocess
import sys

import cherrypy
import configargparse

from minarca_quota_api.zfs_quota import set_quota, get_quota, \
    is_project_quota_enabled


def _parse_args(args):
    parser = configargparse.ArgParser(
        prog='minarca-quota-api',
        description='Web server to manage user quota.',
        default_config_files=['/etc/minarca/minarca-quota-api.conf', '/etc/minarca/minarca-quota-api.conf.d/*.conf'],
        add_env_var_help=True, auto_env_var_prefix='MINARCA_QUOTA_')
    parser.add('-f', '--config', is_config_file=True, help='configuration file path')

    parser.add('--serverhost', metavar='IP', help='Define the IP address to listen to.', default='127.0.0.1')
    parser.add('--serverport', metavar='PORT', help='Define the port to listen to.', default='8081', type=int)
    parser.add('--logfile', metavar='FILE', help='Define the location of the log file.', default='')
    parser.add('--logaccessfile', metavar='FILE', help='Define the location of the access log file.', default='')
    parser.add('--pool', '--zfs-pool', metavar='POOL', help="Define the ZFS pool to be updated with user's quota.", default='rpool/minarca')
    parser.add('--secret', metavar='SECRET', help="Secret to be used to authenticate to the service.", default='secret')
    return parser.parse_args(args)


def _error_page(**kwargs):
    """
    Custom error page to return plain text error message.
    """
    cherrypy.response.headers['Content-Type'] = 'text/plain'
    return kwargs.get('message')


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
        assert isinstance(user, str) or isinstance(user, bytes) and user
        user = int(user)
        if size:
            size = int(size)

        if cherrypy.request.method in ['PUT', 'POST']:
            cherrypy.log('update user [%s] quota [%s]' % (user, size))
            set_quota(projectid=user, pool=self.pool, quota=size)

        cherrypy.log('get user [%s] quota' % user)
        return get_quota(projectid=user, pool=self.pool)


def run(args=None):
    args = _parse_args(sys.argv[1:] if args is None else args)

    # Configure authentication.
    checkpassword = cherrypy.lib.auth_basic.checkpassword_dict({'minarca': args.secret})  # @UndefinedVariable
    basic_auth = {'tools.auth_basic.on': True,
                  'tools.auth_basic.realm': 'earth',
                  'tools.auth_basic.checkpassword': checkpassword,
                  'tools.auth_basic.accept_charset': 'UTF-8',
    }
    app_config = { '/' : basic_auth }

    # configure web server
    cherrypy.config.update({
        'server.socket_host': args.serverhost,
        'server.socket_port': args.serverport,
        'log.access_file':  args.logaccessfile,
        'log.error_file':  args.logfile,
        'error_page.default': _error_page,
        'environment': 'production',
    })

    # Check if ZFS project quota is enabled.
    if not is_project_quota_enabled(pool=args.pool):
        cherrypy.log("ZFS project quota is not enabled for the pool %s. pool and or dataset must be upgraded" % args.pool)

    # start app
    cherrypy.quickstart(Root(pool=args.pool), '/', config=app_config)


if __name__ == '__main__':  # Script executed directly?
    run()
