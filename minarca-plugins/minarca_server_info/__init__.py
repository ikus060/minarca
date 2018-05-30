#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2018 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import unicode_literals

import cherrypy
from future.utils import native_str
import logging
import os
import os.path
import pkg_resources

from rdiffweb.dispatch import static, empty
from rdiffweb.rdw_config import Option
from rdiffweb.rdw_plugin import ITemplateFilterPlugin


logger = logging.getLogger(__name__)


class MinarcaServerInfo(ITemplateFilterPlugin):
    """
    This plugin allow a user to fetch the server server info.
    """

    ssh_public_key_files = Option("MinarcaSSHPublicKey", default='/etc/ssh/ssh_host_dsa_key.pub,/etc/ssh/ssh_host_ecdsa_key.pub,/etc/ssh/ssh_host_rsa_key.pub', doc="Location to the SSH Server key to be used by the client")

    public_hostname = Option("MinarcaPublicHostname", default='minarca.net', doc="")

    def activate(self):
        self.app.root.api.server_info = self.server_info

    def _ssh_public_key(self):
        """
        Get all ssh public key into a single single.
        """
        # Read all the file one by one.
        body = ''
        files = self.ssh_public_key_files.split(',')
        for filename in files:
            if not os.path.isfile(filename):
                logger.warn("ssh public key file %s doesn't exists", filename)
                continue
            with open(filename, 'r') as f:
                body += f.read()
                if body[-1] != '\n':
                    body += '\n'
        return body

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def server_info(self):
        return {
            'ssh_public_key': self._ssh_public_key(),
            'hostname': self.public_hostname,
        }



