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

USERS = {'minarca': os.environ.get('MINARCA_QUOTA_SECRET', 'secret')}

POOL = os.environ.get('MINARCA_QUOTA_POOL', 'rpool/minarca')


def _getpwnam(user):
    assert isinstance(user, str)
    return pwd.getpwnam(user)


def validate_password(realm, username, password):
    if username in USERS and USERS[username] == password:
        return True
    return False


@cherrypy.tools.auth_basic(realm='minarca-api', checkpassword=validate_password)
class Root(object):

    @cherrypy.expose
    def index(self):
        return 'Minarca Quota API'

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def quota(self, user, size=None):
        assert isinstance(user, str) or isinstance(user, bytes) and user
        if isinstance(user, bytes):
            user = user.decode('utf-8')
        if size:
            size = int(size)

        if cherrypy.request.method in ['PUT', 'POST']:
            return self.set_quota(user, size)
        else:
            return self.get_quota(user)

    def get_quota(self, user):
        """Get user disk quota and space."""

        # Get value using zfs (as exact value).
        args = ['/sbin/zfs', 'get', '-p', '-H', '-o', 'value', 'userused@%s,userquota@%s,used,available' % (user, user), POOL]
        cherrypy.log('get user [%s] quota' % user)
        cherrypy.log('execute command line: %s' % ' '.join(args))
        try:
            output = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            cherrypy.log(e.output)
            raise cherrypy.HTTPError(500, 'fail to get user quota')

        values = output.splitlines()
        if len(values) != 4:
            cherrypy.log('fail to get user disk space: %s' % (output,), severity=logging.ERROR)
            raise cherrypy.HTTPError(500, 'fail to get user quota')
        userused, userquota, used, available = [0 if x == '-' else int(x) for x in values]

        # If size is 0, the user doesn't have a quota.
        if userquota:
            return {"size": userquota, "used": userused, "avail": max(0, userquota - userused)}
        else:
            return {"size": used + available, "used": used, "avail": available}

    def set_quota(self, user, quota):
        """Update the user quota. Return True if quota update is successful."""

        # Get user id (also check if local user).
        try:
            uid = _getpwnam(user).pw_uid
        except KeyError:
            raise cherrypy.HTTPError(500, 'invalid user')

        # Check if system user (for security)
        if uid < 1000:
            cherrypy.log('user quota cannot be set for system user [%s]' % user)
            raise cherrypy.HTTPError(500, 'invalid user')

        cherrypy.log('update user [%s] quota [%s]' % (user, quota))
        args = ['/sbin/zfs', 'set', 'userquota@%s=%s' % (user, quota), POOL]
        cherrypy.log('execute command line: %s' % ' '.join(args))
        try:
            subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            cherrypy.log(e.output)
            raise cherrypy.HTTPError(500, 'fail to set user quota')
        # Return the new quota value.
        return self.get_quota(user)


def run():
    cherrypy.config.update({
        'server.socket_host': os.environ.get('MINARCA_QUOTA_HOST', '127.0.0.1'),
        'server.socket_port': int(os.environ.get('MINARCA_QUOTA_PORT', '8081')),
    })
    cherrypy.quickstart(Root(), '/')
