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

    def _get_disk_space(self, user):
        """Get disk space. Take quota in consideration."""

        # Get disk usages from filesystem
        disk_space = self._get_fs_disk_space(user)
        if not disk_space:
            return False

        # Take quota in consideration.
        user_setup_plugin = self.app.plugins.get_by_name('MinarcaUserSetup')
        if user_setup_plugin:
            user_setup = user_setup_plugin.plugin_object
            quota = user_setup.get_userquota(user)
            if quota:
                disk_space['avail'] = min(disk_space['avail'], quota)

        return disk_space

    def _get_fs_disk_space(self, user):
        """
        Get current user disk space usage.
        """
        logger.debug("get disk space usages for [%s]", user)
        # On linux use statvfs()
        # FIXME statvfs is not available on python3
        rootdir = self.app.currentuser.root_dir
        if not rootdir:
            return False
        try:
            data = os.statvfs(rootdir)
        except:
            return False
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
        user = self.app.currentuser.username
        if not user:
            raise ValueError("user is not defined, can't get disk usages")

        # Append disk usage info
        params["minarca_disk_space"] =  = self._get_disk_space(user)

        # Append our template
        template = self.app.templates.get_template("minarca_disk_space.html")
        params["templates_before_content"].append(template)
