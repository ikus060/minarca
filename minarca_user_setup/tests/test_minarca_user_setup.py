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
        self.assertEquals('bob@test.com', self.app.userdb.get_user('bob').email)
        self.assertEquals('/tmp/bob', self.app.userdb.get_user('bob').user_root)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
