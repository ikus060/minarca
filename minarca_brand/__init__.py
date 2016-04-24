#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca disk space rdiffweb plugin
#
# Copyright (C) 2015 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import unicode_literals

from future.utils import native_str
import pkg_resources
from rdiffweb.rdw_plugin import IRdiffwebPlugin
import cherrypy
from cherrypy.lib.static import serve_file
from rdiffweb.dispatch import static


class MinarcaBrand(IRdiffwebPlugin):
    """
    This plugin update the configuration to use a different header name and
    logo.
    """
    def activate(self):
        # Override location of main.css
        path = pkg_resources.resource_filename('minarca_brand', 'minarca.css')  # @UndefinedVariable
        self.app.root.static.main_css = static(path)
        # Activate plugin.
        IRdiffwebPlugin.activate(self)
