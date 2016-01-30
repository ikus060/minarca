#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca disk space rdiffweb plugin
#
# Copyright (C) 2015 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
"""
Created on Oct 20, 2015

@author: ikus060
"""

from __future__ import unicode_literals

from builtins import str
import logging
import mock
from mockldap import MockLdap
import shutil
import tempfile
import unittest

from rdiffweb.test import WebCase, AppTestCase


class TestMinarcaUserSetup(WebCase):

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
        'objectClass': ['person', 'organizationalPerson', 'inetOrgPerson', 'posixAccount']})
    kim = ('uid=kim,ou=People,dc=nodomain', {
        'uid': ['kim'],
        'cn': ['kim'],
        'userPassword': ['password'],
        'homeDirectory': '/tmp/kim',
        'mail': ['kim@test.com'],
        'description': ['v7', 'vfoo', 'coucou'],
        'objectClass': ['person', 'organizationalPerson', 'inetOrgPerson', 'posixAccount']})

    # This is the content of our mock LDAP directory. It takes the form
    # {dn: {attr: [value, ...], ...}, ...}.
    directory = dict([
        basedn,
        people,
        bob,
        kim
    ])

    login = True

    reset_app = True

    @classmethod
    def setup_server(cls):
        WebCase.setup_server(enabled_plugins=['SQLite', 'MinarcaUserSetup', 'Ldap'])

    def setUp(self):

        # Mock LDAP
        self.mockldap = MockLdap(self.directory)
        self.mockldap.start()
        self.ldapobj = self.mockldap['ldap://localhost/']
        # Reconfigure
        self.basedir = str(tempfile.mkdtemp(prefix='minarca_user_setup_tests_'))
        self.app.cfg.set_config('MinarcaUserSetupBaseDir', self.basedir)
        # Call parent implementation
        WebCase.setUp(self)

    def tearDown(self):
        # Stop patching ldap.initialize and reset state.
        self.mockldap.stop()
        del self.ldapobj
        del self.mockldap
        # Delete temp directory
        shutil.rmtree(self.basedir)
        # Call parent implementation
        WebCase.tearDown(self)

    def _get_plugin_obj(self):
        return self.app.plugins.get_plugin_by_name('MinarcaUserSetup')

    def test_check_plugin_enabled(self):
        """
        Check if the plugin is shown in plugins page.
        """
        self.getPage("/admin/plugins/")
        self.assertInBody('MinarcaUserSetup')

    def test_add_user(self):
        """
        Check if new user is created with user_root and email.
        """
        self.app.userdb.add_user('bob')
        self.assertTrue(self.app.userdb.exists('bob'))
        self.assertEquals('bob@test.com', self.app.userdb.get_email('bob'))
        self.assertEquals('/tmp/bob', self.app.userdb.get_user_root('bob'))

    def test_get_ldap_userquota(self):
        """Check number of bytes return for v7."""
        # 7GiB
        self.assertEquals(7516192768, self._get_plugin_obj().get_ldap_userquota('kim'))

    def test_get_ldap_userquota_without_description(self):
        """Check if return False when no matching description found."""
        self.assertFalse(self._get_plugin_obj().get_ldap_userquota('bob'))


class TesZfstMinarcaUserSetup(AppTestCase):

    reset_app = True

    enabled_plugins = ['SQLite', 'MinarcaUserSetup']

    default_config = {
        'MinarcaUserSetupBaseDir': '/tmp',
        'MinarcaUserSetupZfsPool': 'tank',
    }

    # run before each test - the mock_popen will be available and in the right state in every test<something> function
    def setUp(self):
        AppTestCase.setUp(self)

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
        AppTestCase.tearDown(self)

    def _get_plugin_obj(self):
        return self.app.plugins.get_plugin_by_name('MinarcaUserSetup')

    def test_get_zfs_diskspace_no_quota(self):
        """Check value for zfs disk space usage."""
        self.mock_rv.communicate.return_value[0] = """26112\n0\n284783104\n16228191744"""
        self.assertEquals(
            {'size': 16512974848, 'used': 284783104, 'avail': 16228191744},
            self._get_plugin_obj().get_zfs_diskspace('root'))

    def test_get_zfs_diskspace_with_quota(self):
        """Check value for zfs disk space usage."""
        self.mock_rv.communicate.return_value[0] = """0\n53687091200\n284761600\n16228213248"""
        self.assertEquals(
            {'size': 53687091200, 'used': 0, 'avail': 53687091200},
            self._get_plugin_obj().get_zfs_diskspace('root'))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
