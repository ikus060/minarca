# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import logging
import os
from io import open
from urllib.parse import urlparse

import cherrypy
import pkg_resources
from rdiffweb.rdw_app import RdiffwebApp

import minarca_server.plugins.minarca  # noqa
from minarca_server.config import parse_args

# Define logger for this module
logger = logging.getLogger(__name__)


class MinarcaApplication(RdiffwebApp):
    @classmethod
    def parse_args(cls, args=None, config_file_contents=None):
        return parse_args(args, config_file_contents)

    def __init__(self, cfg):
        cherrypy.config.update(
            {
                'minarca.auth_options': cfg.minarca_auth_options,
                'minarca.help_url': cfg.minarca_help_url,
                'minarca.quota_api_url': cfg.minarca_quota_api_url,
                'minarca.remote_host': cfg.minarca_remote_host,
                'minarca.remote_host_identity': cfg.minarca_remote_host_identity,
                'minarca.restricted_to_base_dir': cfg.minarca_restricted_to_base_dir,
                'minarca.shell': cfg.minarca_shell,
                'minarca.user_base_dir': cfg.minarca_user_base_dir,
                'minarca.user_dir_group_id': cfg.minarca_user_dir_group,
                'minarca.user_dir_mode': cfg.minarca_user_dir_mode,
                'minarca.user_dir_owner_id': cfg.minarca_user_dir_owner,
            }
        )
        super().__init__(cfg)
        # Add few pages.
        self.root.api.minarca = self.get_minarca
        self.root.help = self.get_help

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_minarca(self):

        # RemoteHost
        remotehost = self.cfg.minarca_remote_host
        if not remotehost:
            remotehost = urlparse(cherrypy.request.base).hostname

        # Identity known_hosts
        identity = ""
        files = [
            f
            for f in os.listdir(self.cfg.minarca_remote_host_identity)
            if f.startswith('ssh_host')
            if f.endswith('.pub')
        ]
        for fn in files:
            with open(os.path.join(self.cfg.minarca_remote_host_identity, fn)) as fh:
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

    @cherrypy.expose
    @cherrypy.tools.i18n(on=False)
    @cherrypy.tools.sessions(on=False)
    @cherrypy.tools.auth_mfa(on=False)
    @cherrypy.tools.auth_form(on=False)
    def get_help(self):
        raise cherrypy.HTTPRedirect(self.cfg.minarca_help_url)

    @property
    def version(self):
        """
        Get the current running version (using package info).
        """
        return minarca_server.__version__
