# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import os
from urllib.parse import urlparse

import cherrypy
import pkg_resources
from cherrypy.lib.auth_basic import basic_auth
from rdiffweb.controller.api import ApiPage, _checkpassword
from rdiffweb.core.model import SshKey, UserObject

from minarca_server.core.minarcaid import verify_minarcaid


def _public_key_lockup(fingerprint):
    """
    Search database for matching key and username.
    """
    row = (
        SshKey.query.with_entities(SshKey.key, UserObject.username)
        .join(UserObject, SshKey.userid == UserObject.userid)
        .filter(SshKey.fingerprint == fingerprint)
        .first()
    )
    if row is None:
        return None
    # Return a tuple.
    return (row.key, row.username)


def minarca_auth(realm):
    """
    Minarca specific implementation to authenticate against minarcaid or basic username password.
    """
    auth_header = cherrypy.request.headers.get('authorization')
    if auth_header is not None and auth_header.lower().startswith('minarcaid '):
        # split() error
        minarcaid = auth_header.split(' ', 1)[1]
        # Get all valid public keys.
        try:
            # If valid, define scope as write_user to allow editing user's settings only.
            public_key, username = verify_minarcaid(minarcaid, _public_key_lockup)
            cherrypy.request.login = username
            cherrypy.serving.request.scope = ['write_user']
            return  # successful authentication
        except ValueError as e:
            cherrypy.log('Minarcaid auth fail: %s' % str(e), 'TOOLS.MINARCA_AUTH')
            # Respond with 401 status and a WWW-Authenticate header
            cherrypy.serving.response.headers['www-authenticate'] = 'Basic realm="%s"' % realm
            raise cherrypy.HTTPError(401, 'You are not authorized to access that resource')

    # Fallback to basic_auth
    basic_auth(realm, _checkpassword)


cherrypy.tools.minarca_auth = cherrypy.Tool('before_handler', minarca_auth, priority=70)


# Replace basic auth by our custom implementation
@cherrypy.tools.auth_basic(on=False)
@cherrypy.tools.minarca_auth(realm='minarca')
class MinarcaApiPage(ApiPage):
    """
    Replacement of /api for Minarca server
    """

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def minarca(self):
        # RemoteHost
        cfg = self.app.cfg
        remotehost = cfg.minarca_remote_host
        if not remotehost:
            remotehost = urlparse(cherrypy.request.base).hostname

        # Identity known_hosts
        identity = ""
        files = [
            f for f in os.listdir(cfg.minarca_remote_host_identity) if f.startswith('ssh_host') if f.endswith('.pub')
        ]
        for fn in files:
            with open(os.path.join(cfg.minarca_remote_host_identity, fn)) as fh:
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
