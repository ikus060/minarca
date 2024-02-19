# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import logging

import cherrypy
import pkg_resources
from rdiffweb.controller.dispatch import staticfile
from rdiffweb.rdw_app import RdiffwebApp

import minarca_server.plugins.minarca  # noqa
from minarca_server.config import parse_args
from minarca_server.controller.api import MinarcaApiPage

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
        cherrypy.config.update(
            {
                'notification.current_version': self.version,
            }
        )
        # Replace API to support additional endpoint and authentication method.
        self.root.api = MinarcaApiPage()
        # Provide /help
        self.root.help = self.get_help
        # Add background
        self.root.static.bg_jpg = staticfile(pkg_resources.resource_filename(__name__, 'bg.jpg'))

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
