#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (C) 2017 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
"""
Created on Nov 16, 2017

@author: ikus060
"""

from __future__ import unicode_literals

import pkg_resources
import unittest

from rdiffweb.test import WebCase


class MinarcaServerInfoTest(WebCase):

    login = True

    reset_app = True

    @classmethod
    def setup_server(cls,):
        WebCase.setup_server(enabled_plugins=['SQLite', 'MinarcaServerInfo'])

    def setUp(self):
        # Reconfigure
        filename = pkg_resources.resource_filename(__name__, 'test.pub')  # @UndefinedVariable
        self.app.cfg.set_config('MinarcaSSHKPublicey', filename)
        # Call parent implementation
        WebCase.setUp(self)

    def test_server_info(self):
        data = self.getJson("/api/server_info")
        # Check ssh key
        self.assertIn('ssh_public_key', data)
        self.assertIn('ssh-rsa', data['ssh_public_key'])
        # Check hostname
        self.assertIn('hostname', data)
        self.assertEqual('minarca.net', data['hostname'])


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
