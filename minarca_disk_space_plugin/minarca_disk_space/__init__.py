#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca disk space rdiffweb plugin
#
# Copyright (C) 2015 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import unicode_literals

import logging
import os

from rdiffweb.rdw_plugin import ILocationsPagePlugin  # @UnresolvedImport

# Define logger for this module
logger = logging.getLogger(__name__)


class MinarcaDiskSpace(ILocationsPagePlugin):
    """
    This plugin provide feedback information to the users about the disk usage.
    Since we define quota, this plugin display the user's quota.
    """

    def _get_disk_space(self):
        """
        Get current user disk space usage.
        """
        # Get reference to current user.
        username = self.app.currentuser.username
        if username is None:
            raise ValueError("username is not defined, can't get disk usages.")

        logger.debug("get disk space usages for [%s]", username)
        # On linux use statvfs()
        # FIXME statvfs is not available on python3
        rootdir = self.app.currentuser.root_dir
        if not rootdir:
            return dict()
        try:
            data = os.statvfs(rootdir)
        except:
            return dict()
        # Compute the space.
        size = data.f_frsize * data.f_blocks
        avail = data.f_frsize * data.f_bavail
        used = size - avail
        # Return dictionary with values.
        return {"size": size, "used": used, "avail": avail}

    def locations_update_params(self, params):
        """
        This method is called to add extra param to the locations page.
        """

        # Append disk usage info
        disk_space = self._get_disk_space()
        if disk_space:
            params["minarca_disk_space"] = disk_space

        # Append our template
        template = self.app.templates.get_template("minarca_disk_space.html")
        params["templates_before_content"].append(template)
