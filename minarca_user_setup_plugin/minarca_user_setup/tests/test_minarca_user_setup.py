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
import mock
from mockldap import MockLdap

from rdiffweb.test import MockRdiffwebApp

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
    kim = (b'uid=kim,ou=People,dc=nodomain', {
        b'uid': [b'kim'],
        b'cn': [b'kim'],
        b'userPassword': [b'password'],
        b'homeDirectory': b'/tmp/kim',
        b'mail': [b'kim@test.com'],
        b'description': [b'v7', b'vfoo', b'coucou'],
        b'objectClass': [b'person', b'organizationalPerson', b'inetOrgPerson', b'posixAccount']})

    # This is the content of our mock LDAP directory. It takes the form
    # {dn: {attr: [value, ...], ...}, ...}.
    directory = dict([
        basedn,
        people,
        bob,
        kim
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
        self.plugin_info = self.app.plugins.get_plugin_by_name('MinarcaUserSetup')
        self.assertIsNotNone(self.plugin_info)
        self.plugin_obj = self.plugin_info.plugin_object
        self.assertIsNotNone(self.plugin_obj)

    def tearDown(self):
        # Stop patching ldap.initialize and reset state.
        self.mockldap.stop()
        del self.ldapobj

    def test_add_user(self):
        self.app.userdb.add_user('bob')
        self.assertTrue(self.app.userdb.exists('bob'))
        self.assertEquals('bob@test.com', self.app.userdb.get_email('bob'))
        self.assertEquals('/tmp/bob', self.app.userdb.get_user_root('bob'))

    def test_get_ldap_userquota(self):
        """Check number of bytes return for v7."""
        # 7GiB
        self.assertEquals(7516192768, self.plugin_obj.get_ldap_userquota('kim'))

    def test_get_ldap_userquota_without_description(self):
        """Check if return False when no matching description found."""
        self.assertFalse(self.plugin_obj.get_ldap_userquota('bob'))


class TesZfstMinarcaUserSetup(unittest.TestCase):

    # run before each test - the mock_popen will be available and in the right state in every test<something> function
    def setUp(self):
        # Mock Application
        search_path = pkg_resources.resource_filename('minarca_user_setup', '..')  # @UndefinedVariable
        self.app = MockRdiffwebApp(
            enabled_plugins=['SQLite', 'MinarcaUserSetup'],
            default_config={
                'PluginSearchPath': search_path,
                'MinarcaUserSetupBaseDir': '/tmp',
                'MinarcaUserSetupZfsPool': 'tank'})
        self.app.reset()

        # Check if plugin loaded
        self.plugin_info = self.app.plugins.get_plugin_by_name('MinarcaUserSetup')
        self.assertIsNotNone(self.plugin_info)
        self.plugin_obj = self.plugin_info.plugin_object
        self.assertIsNotNone(self.plugin_obj)

        # The "where to patch" bit is important - http://www.voidspace.org.uk/python/mock/patch.html#where-to-patch
        self.popen_patcher = mock.patch('minarca_user_setup.subprocess.Popen')
        self.mock_popen = self.popen_patcher.start()

        self.mock_rv = mock.Mock()
        # communicate() returns [STDOUT, STDERR]
        self.mock_rv.communicate.return_value = [None, None]
        self.mock_popen.return_value = self.mock_rv

    # run after each test
    def tearDown(self):
        self.popen_patcher.stop()

    def test_get_zfs_diskspace_no_quota(self):
        """Check value for zfs disk space usage."""
        self.mock_rv.communicate.return_value[0] = """26112\n0\n284783104\n16228191744"""
        self.assertEquals(
            {'size': 16512974848, 'used': 284783104, 'avail': 16228191744},
            self.plugin_obj.get_zfs_diskspace('root'))

    def test_get_zfs_diskspace_with_quota(self):
        """Check value for zfs disk space usage."""
        self.mock_rv.communicate.return_value[0] = """0\n53687091200\n284761600\n16228213248"""
        self.assertEquals(
            {'size': 53687091200, 'used': 0, 'avail': 53687091200},
            self.plugin_obj.get_zfs_diskspace('root'))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
