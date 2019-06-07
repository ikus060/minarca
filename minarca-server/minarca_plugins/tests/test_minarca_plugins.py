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

from io import open
import logging
import os
from rdiffweb.test import WebCase, AppTestCase
import shutil
import tempfile
import unittest

import httpretty
from mock.mock import MagicMock  # @UnresolvedImport
from mockldap import MockLdap
import pkg_resources

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


class MinarcaSshKeysTest(AppTestCase):
    """
    Collections of tests related to ssh keys file update.
    """
    USERNAME = 'admin'

    PASSWORD = 'test'
    
    base_dir = tempfile.mkdtemp(prefix='minarca_tests_')
    
    default_config = { 'MinarcaUserBaseDir': base_dir }
    
    def setUp(self):
        AppTestCase.setUp(self)
        if not os.path.isdir(self.base_dir):
            os.mkdir(self.base_dir)
    
    def tearDown(self):
        shutil.rmtree(self.base_dir)
        AppTestCase.tearDown(self)
    
    def test_update_authorized_keys(self):
        self.plugin = MinarcaUserSetup(self.app)
        self.plugin._update_authorized_keys()
    
    def test_add_key(self):
        """
        Test creation of the ssh key.
        """
        # Read the key from a file
        filename = pkg_resources.resource_filename(__name__, 'test_publickey_ssh_rsa.pub')  # @UndefinedVariable
        with open(filename, 'r', encoding='utf8') as f: 
            key = f.readline()
        
        # Add the key to the user.
        userobj = self.app.userdb.get_user('admin')
        userobj.add_authorizedkey(key)
        
        # Validate
        filename = os.path.join(self.base_dir, '.ssh', 'authorized_keys')
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()
        self.assertEquals(
            'command="/opt/minarca/bin/minarca-shell admin",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDDYeMPTCnRLFaLeSzsn++RD5jwuuez65GXrt9g7RYUqJka66cn7zHUhjDWx15fyEM3ikHGbmmWEP2csq11YCtvaTaz2GAnwcFNdt2NF0KGHMbE56Xq0eCkj1FCait/UyRBqkaFItYAoBdj4War9Xt+S5sV8qc5/TqTeku4Kg6ZBJRFCDHy6nR8Xf+tXiBrlfCnXvxamDI5kFP0B+npuBv+M4TjKFvwn5W8zYPPTEznilWnGvJFS71XwsOD/yHBGQb/Jz87aazNAeCznZRAJxfecJhgeChGZcGnXRAAdEeMbRyilYWaNquIpwrbNFElFlVf41EoDBk6woB8TeG0XFfz ikus060@ikus060-t530\n',
            data)
    

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
