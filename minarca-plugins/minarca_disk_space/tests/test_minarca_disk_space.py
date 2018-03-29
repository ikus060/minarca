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

import httpretty
import logging
from mock.mock import MagicMock
from mockldap import MockLdap
import unittest

from rdiffweb.test import WebCase


class MinarcaDiskSpaceTest(WebCase):

    # Reset app and testcases on every test
    reset_app = True
    reset_testcases = False

    # Disable interactive mode.
    interactive = False

    # Data for LDAP mock.
    basedn = ('dc=nodomain', {
        'dc': ['nodomain'],
        'o': ['nodomain']})
    people = ('ou=People,dc=nodomain', {
        'ou': ['People'],
        'objectClass': ['organizationalUnit']})
    bob = ('uid=bob,ou=People,dc=nodomain', {
        'uid': ['bob'],
        'cn': ['bob'],
        'userPassword': ['password'],
        'homeDirectory': '/tmp/bob',
        'mail': ['bob@test.com'],
        'description': ['v2'],
        'objectClass': ['person', 'organizationalPerson', 'inetOrgPerson', 'posixAccount']})

    # This is the content of our mock LDAP directory. It takes the form
    # {dn: {attr: [value, ...], ...}, ...}.
    directory = dict([
        basedn,
        people,
        bob,
    ])

    @classmethod
    def setup_server(cls,):
        WebCase.setup_server(enabled_plugins=['SQLite', 'MinarcaDiskSpace', 'Ldap'], default_config={'AddMissingUser': 'true'})

    def setUp(self):
        self.app.userdb.get_user('admin').user_root = '/tmp'
        # Mock LDAP
        self.mockldap = MockLdap(self.directory)
        self.mockldap.start()
        self.ldapobj = self.mockldap['ldap://localhost/']
        WebCase.setUp(self)
        self.plugin = self.app.plugins.get_plugin_by_name('MinarcaDiskSpace')

    def tearDown(self):
        # Stop patching ldap.initialize and reset state.
        self.mockldap.stop()
        del self.ldapobj
        del self.mockldap

    def test_check_plugin_enabled(self):
        """
        Check if the plugin is shown in plugins page.
        """
        self._login(self.USERNAME, self.PASSWORD)
        self.getPage("/admin/plugins/")
        self.assertInBody('MinarcaDiskSpace')

    def test_get_ldap_userquota(self):
        quota = self.plugin._get_ldap_userquota('bob')
        self.assertEquals(2147483648, quota)

    @httpretty.activate
    def test__update_userquota(self):
        httpretty.register_uri(httpretty.POST, "http://localhost:8081/quota/bob",
                               body='{"avail": 2147483648, "used": 0, "size": 2147483648}')
        self.plugin._update_userquota('bob')

    @httpretty.activate
    def test__update_userquota_401(self):
        # Checks if exception is raised when authentication is failing.
        httpretty.register_uri(httpretty.POST, "http://localhost:8081/quota/bob",
                               status=401)
        # Make sure an exception is raised.
        with self.assertRaises(Exception):
            self.plugin._update_userquota('bob')

    def test_get_usage_info(self):
        """
        Check if value is available.
        """
        self.plugin._update_userquota = MagicMock(return_value={"avail": 2147483648, "used": 0, "size": 2147483648})

        self._login('bob', 'password')

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


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
