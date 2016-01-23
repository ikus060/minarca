#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca disk space rdiffweb plugin
#
# Copyright (C) 2015 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
"""
Created on Jan 23, 2016

@author: ikus060
"""

from __future__ import unicode_literals

import logging
import pkg_resources
import unittest

from rdiffweb.test import WebCase


class MinarcaDiskSpaceTest(WebCase):

    login = True

    reset_app = True

    @classmethod
    def setup_server(cls,):
        path = pkg_resources.resource_filename('minarca_disk_space', '..')  # @UndefinedVariable
        WebCase.setup_server(enabled_plugins=['SQLite', 'MinarcaDiskSpace'], default_config={'PluginSearchPath': path})

    def setUp(self):
        WebCase.setUp(self)
        self.app.userdb.set_user_root('admin', '/tmp')

    def test_check_plugin_enabled(self):
        """
        Check if the plugin is shown in plugins page.
        """
        self.getPage("/admin/plugins/")
        self.assertInBody('MinarcaDiskSpace')

    def test_get_usage_info(self):
        """
        Check if value is available.
        """

        self.getPage("/")
        # Check if template is loaded
        self.assertInBody('Usage')
        self.assertInBody('used')
        self.assertInBody('total')
        self.assertInBody('free')
        # Check if meta value is available
        self.assertInBody('freeSpace')
        self.assertInBody('occupiedSpace')
        self.assertInBody('totalSpace')

    def test_get_usage_info_fr(self):
        """
        Check if translation is loaded.
        """

        self.getPage("/", headers=[("Accept-Language", "fr-CA;q=0.8,fr;q=0.6")])
        # Check if template is loaded
        self.assertInBody('Utilisation')
        self.assertInBody('utilisé')
        self.assertInBody('disponible')
        # Check if meta value is available
        self.assertInBody('freeSpace')
        self.assertInBody('occupiedSpace')
        self.assertInBody('totalSpace')


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
