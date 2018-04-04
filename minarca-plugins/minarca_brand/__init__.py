#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca disk space rdiffweb plugin
#
# Copyright (C) 2018 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import unicode_literals

import cherrypy
from future.utils import native_str
import os
import pkg_resources

from rdiffweb.dispatch import static
from rdiffweb.rdw_plugin import ITemplateFilterPlugin


class MinarcaBrand(ITemplateFilterPlugin):
    """
    This plugin update the configuration to use a different header name and
    logo.
    """
    def activate(self):
        # Override the favicon
        favicon = pkg_resources.resource_filename('minarca_brand', 'static/minarca.ico')  # @UndefinedVariable
        self.app.root.favicon_ico = static(favicon)

        # Activate plugin.
        ITemplateFilterPlugin.activate(self)

    def filter_data(self, template_name, data):
        if template_name.endswith('.html'):
            # Append our template
            template = self.app.templates.get_template("minarca_head.html")
            data["extra_head_templates"].append(template)
            # Add our branding
            data['header_logo'] = '/minarca_brand_static/minarca_22_w.png'
            data['main_css'] = '/minarca_brand_static/minarca.css'
