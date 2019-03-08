#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca disk space rdiffweb plugin
#
# Copyright (C) 2019 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
"""
Created on Jan 23, 2016

@author: Patrik Dufresne
"""

from __future__ import unicode_literals

import logging
from rdiffweb.test import WebCase
import unittest

import httpretty
from mock.mock import MagicMock  # @UnresolvedImport
from mockldap import MockLdap

from minarca_plugins import MinarcaUserSetup


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
    def setup_server(cls):
        WebCase.setup_server(default_config={
            'AddMissingUser': 'true',
            'LdapUri': '__default__',
            'LdapBaseDn': 'dc=nodomain',
            })

    def setUp(self):
        self.app.userdb.get_user('admin').user_root = '/tmp'
        # Mock LDAP
        self.mockldap = MockLdap(self.directory)
        self.mockldap.start()
        self.ldapobj = self.mockldap['ldap://localhost/']
        WebCase.setUp(self)
        self.plugin = MinarcaUserSetup(self.app)

    def tearDown(self):
        # Stop patching ldap.initialize and reset state.
        self.mockldap.stop()
        del self.ldapobj
        del self.mockldap

    def test_login(self):
        """
        Check if new user is created with user_root and email.
        """
        userobj = self.app.userdb.login('bob', 'password')
        self.assertIsNotNone(userobj)
        self.assertTrue(self.app.userdb.exists('bob'))
        # Check if profile get update from Ldap info.
        self.assertEquals('bob@test.com', self.app.userdb.get_user('bob').email)
        self.assertEquals('/tmp/bob', self.app.userdb.get_user('bob').user_root)

    @httpretty.activate
    def test_set_disk_quota(self):
        httpretty.register_uri(httpretty.POST, "http://localhost:8081/quota/bob",
                               body='{"avail": 2147483648, "used": 0, "size": 2147483648}')
        userobj = self.app.userdb.add_user('bob')
        self.plugin.set_disk_quota(userobj, quota=1234567)

    @httpretty.activate
    def test_update_userquota_401(self):
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
