#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca Quota API
#
# Copyright (C) 2019 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
"""
Created on Mar 7, 2018

@author: Patrik Dufresne
"""

from __future__ import unicode_literals

from builtins import str, bytes
import cherrypy
from future.utils.surrogateescape import encodefilename
import logging
import os
import pwd
import subprocess
import sys

PY3 = sys.version_info[0] == 3

USERS = {'minarca': os.environ.get('MINARCA_QUOTA_SECRET', 'secret')}

POOL = os.environ.get('MINARCA_QUOTA_POOL', 'rpool/minarca')


def _getpwnam(user):
    assert isinstance(user, str)
    if PY3:
        return pwd.getpwnam(user)
    else:
        return pwd.getpwnam(encodefilename(user))


def validate_password(realm, username, password):
    if username in USERS and USERS[username] == password:
        return True
    return False


def _call(*args):
    cherrypy.log('execute command line: %s' % ' '.join(args))
    return subprocess.check_output(args)


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
        cherrypy.log('get user [%s] quota' % user)
        user_pool = os.path.join(POOL, user)
        try:
            output = _call('/sbin/zfs', 'get', '-p', '-H', '-o', 'value', 'used,available,quota', user_pool)
        except subprocess.CalledProcessError as e:
            cherrypy.log(e.output)
            raise cherrypy.HTTPError(500, 'fail to get user quota')

        values = output.splitlines()
        if len(values) != 3:
            cherrypy.log('fail to get user disk space: %s' % (output,), severity=logging.ERROR)
            raise cherrypy.HTTPError(500, 'fail to get user quota')
        used, available, quota = [0 if x == '-' else int(x) for x in values]

        # If quota is 0, the user doesn't have a quota.
        if quota:
            return {"size": quota, "used": used, "avail": max(0, quota - used)}
        else:
            return {"size": used + available, "used": used, "avail": available}

    def set_quota(self, user, quota):
        """Update the user quota. Return True if quota update is successful."""

        cherrypy.log('update user [%s] quota [%s]' % (user, quota))
        quota = int(quota)
        user_pool = os.path.join(POOL, user)
        try:
            _call('/sbin/zfs', 'create', user_pool)
        except subprocess.CalledProcessError as e:
            if 'dataset already exists' in e.output:
                pass    
            else:
                raise cherrypy.HTTPError(500, 'fail to get user quota')
        try:
            _call('/sbin/zfs', 'set', 'quota=%s' % quota, user_pool)
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
