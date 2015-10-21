#!/usr/bin/python
# -*- coding: utf-8 -*-
# rdiffweb, A web interface to rdiff-backup repositories
# Copyright (C) 2015 Patrik Dufresne Service Logiciel
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import logging
import pkg_resources
import unittest
from mockldap import MockLdap

from rdiffweb.tests.test import MockRdiffwebApp

"""
Created on Oct 20, 2015

@author: ikus060
"""


class TestMinarcaUserSetup(unittest.TestCase):

    basedn = (b'dc=nodomain', {
        b'dc': [b'nodomain'],
        b'o': [b'nodomain']})
    people = (b'ou=People,dc=nodomain', {
        b'ou': [b'People'],
        b'objectClass': [b'organizationalUnit']})
    bob = (b'uid=bob,ou=People,dc=nodomain', {
        b'uid': [b'bob'],
        b'cn': [b'bob'],
        b'userPassword': [b'password'],
        b'homeDirectory': b'/tmp/bob',
        b'mail': [b'bob@test.com'],
        b'objectClass': [b'person', b'organizationalPerson', b'inetOrgPerson', b'posixAccount']})

    # This is the content of our mock LDAP directory. It takes the form
    # {dn: {attr: [value, ...], ...}, ...}.
    directory = dict([
        basedn,
        people,
        bob
    ])

    @classmethod
    def setUpClass(cls):
        # We only need to create the MockLdap instance once. The content we
        # pass in will be used for all LDAP connections.
        cls.mockldap = MockLdap(cls.directory)

    @classmethod
    def tearDownClass(cls):
        del cls.mockldap

    def setUp(self):
        # Mock LDAP
        self.mockldap.start()
        self.ldapobj = self.mockldap['ldap://localhost/']
        # Mock Application
        search_path = pkg_resources.resource_filename('minarca_user_setup', '..')  # @UndefinedVariable
        self.app = MockRdiffwebApp(enabled_plugins=['SQLite', 'Ldap', 'MinarcaUserSetup'], default_config={'PluginSearchPath': search_path, 'MinarcaUserSetupBaseDir': '/tmp'})
        self.app.reset()
        # Check if plugin loaded
        self.plugin_obj = self.app.plugins.get_plugin_by_name('MinarcaUserSetup')
        self.assertIsNotNone(self.plugin_obj)

    def test_add_user(self):
        self.app.userdb.add_user('bob')
        self.assertTrue(self.app.userdb.exists('bob'))
        self.assertEquals('bob@test.com', self.app.userdb.get_email('bob'))
        self.assertEquals('/tmp/bob', self.app.userdb.get_user_root('bob'))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
