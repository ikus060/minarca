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

import pkg_resources
import unittest

from rdiffweb.test import WebCase


class MinarcaBrandTest(WebCase):

    login = True

    reset_app = True

    @classmethod
    def setup_server(cls,):
        headerlogo = pkg_resources.resource_filename('minarca_brand', 'minarca_22_w.png')  # @UndefinedVariable
        WebCase.setup_server(
            enabled_plugins=['SQLite', 'MinarcaBrand'],
            default_config={'HeaderLogo': headerlogo})

    def test_check_plugin_enabled(self):
        """
        Check if the plugin is shown in plugins page.
        """
        self.getPage("/admin/plugins/")
        self.assertInBody('MinarcaBrand')

    def test_favicon(self):
        """
        Check if favicon is available.
        """
        self.getPage("/favicon.ico")
        self.assertStatus('200 OK')

    def test_header_logo(self):
        """
        Check if header logo available.
        """
        self.getPage("/minarca_22_w.png")
        self.assertStatus('200 OK')


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
