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
from rdiffweb.rdw_plugin import ITemplateFilterPlugin
import cherrypy
from cherrypy.lib.static import serve_file
from rdiffweb.dispatch import static

FILES = ['minarca_16.png', 'minarca_22.png', 'minarca_32.png', 'minarca_48.png', 'minarca.ico', 'minarca_128.png']


class MinarcaBrand(ITemplateFilterPlugin):
    """
    This plugin update the configuration to use a different header name and
    logo.
    """
    def activate(self):
        # Override location of main.css
        path = pkg_resources.resource_filename('minarca_brand', 'minarca.css')  # @UndefinedVariable
        self.app.root.static.main_css = static(path)

        # Also add some static files
        for name in FILES:
            path = pkg_resources.resource_filename('minarca_brand', name)  # @UndefinedVariable
            setattr(self.app.root.static, path.replace('.', '_'), static(path))

        # In development, provide test.html as static page.
        environment = self.app.cfg.get_config('Environment', 'production')
        if environment != 'production':
            path = pkg_resources.resource_filename('minarca_brand', 'test.html')  # @UndefinedVariable
            self.app.root.static.test_html = static(path)
        # Activate plugin.
        ITemplateFilterPlugin.activate(self)

    def filter_data(self, template_name, data):
        if template_name.endswith('.html'):
            # Append our template
            template = self.app.templates.get_template("minarca_head.html")
            data["extra_head_templates"].append(template)
