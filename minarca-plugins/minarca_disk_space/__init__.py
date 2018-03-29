#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca disk space rdiffweb plugin
#
# Copyright (C) 2018 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import unicode_literals

from builtins import str
import cherrypy
import logging
import os
import requests

from rdiffweb import rdw_config
from rdiffweb.rdw_plugin import ITemplateFilterPlugin, IUserChangeListener  # @UnresolvedImport

try:
    from urllib.parse import urljoin  # @UnresolvedImport @UnusedImport
except:
    from urlparse import urljoin  # @UnresolvedImport @UnusedImport @Reimport

# Define logger for this module
logger = logging.getLogger(__name__)


class TimeoutHTTPAdapter(requests.adapters.HTTPAdapter):

    def send(self, *args, **kwargs):
        # Enforce a timeout value if not defined.
        kwargs['timeout'] = kwargs.get('timeout', None)
        return super(TimeoutHTTPAdapter, self).send(*args, **kwargs)


class MinarcaDiskSpace(ITemplateFilterPlugin, IUserChangeListener):
    """
    This plugin provide feedback information to the users about the disk usage.
    Since we define quota, this plugin display the user's quota.
    """

    _quota_api_url = rdw_config.Option('MinarcaQuotaApiUrl', 'http://minarca:secret@localhost:8081/')

    def __init__(self):
        self.session = requests.Session()
        self.session.mount('https://', TimeoutHTTPAdapter(pool_connections=2, pool_maxsize=5))
        self.session.mount('http://', TimeoutHTTPAdapter(pool_connections=2, pool_maxsize=5))

    def filter_data(self, template_name, data):
        if template_name == 'locations.html':
            self._locations_update_params(data)

    def _locations_update_params(self, params):
        """
        This method is called to add extra param to the locations page.
        """
        user = self.app.currentuser.username
        if not user:
            raise ValueError("user is not defined, can't get disk usages")

        # Append disk usage info
        params["minarca_disk_space"] = cherrypy.session.get('user_diskspace')  # @UndefinedVariable

        # Append our template
        template = self.app.templates.get_template("minarca_disk_space.html")
        params["templates_before_content"].append(template)

    def user_logined(self, user, password):
        """
        Need to verify LDAP quota and update ZFS quota if required.
        """
        assert isinstance(user, str)
        # Update the user Quote from LDAP.
        try:
            diskspace = self._update_userquota(user)
            cherrypy.session['user_diskspace'] = diskspace  # @UndefinedVariable
        except:
            logger.warning('fail to update user quota [%s]', user, exc_info=1)

    def _update_userquota(self, user):
        """
        Get quota from LDAP and update the ZFS quota if required.
        """
        # Get user quota from LDAP server.
        quota = self._get_ldap_userquota(user) or 0
        logger.info('user [%s] quota [%s]', user, quota)

        # Always update unless quota not define
        url = os.path.join(self._quota_api_url, 'quota', user)
        if quota:
            diskspace = self.session.post(url, data={'size': quota}, timeout=1).json()
        else:
            diskspace = self.session.get(url, timeout=1).json()
        assert diskspace and isinstance(diskspace, dict) and 'avail' in diskspace and 'used' in diskspace and 'size' in diskspace

        # Keep values in session.
        return diskspace  # @UndefinedVariable

    def _get_ldap_store(self):
        """get reference to ldap_store"""
        plugin = self.app.plugins.get_plugin_by_name('LdapPasswordStore')
        assert plugin
        return plugin

    def _get_ldap_userquota(self, user):
        """Get userquota from LDAP database."""
        assert isinstance(user, str)

        # Get quota value from description field.
        ldap_store = self._get_ldap_store()
        assert ldap_store
        descriptions = ldap_store.get_user_attr(user, 'description')
        if not descriptions:
            return False
        quota_gb = [int(x[1:])
                    for x in descriptions
                    if x.startswith("v") and x[1:].isdigit()]
        if not quota_gb:
            return False
        quota_gb = max(quota_gb)
        return quota_gb * 1024 * 1024 * 1024
