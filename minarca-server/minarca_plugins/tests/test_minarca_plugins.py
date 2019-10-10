#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca server
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


class MinarcaUserSetupTest(WebCase):
    
    # Reset app and testcases on every test
    reset_app = True
    # Login as admin before each test
    login = True
    
    @classmethod
    def setup_server(cls):
        WebCase.setup_server(default_config={
            'MinarcaUserBaseDir': '/tmp/minarca-test',
            })
        
    def setUp(self):
        if not os.path.isdir('/tmp/minarca-test'):
            os.mkdir('/tmp/minarca-test')
        WebCase.setUp(self)

    def tearDown(self):
        WebCase.tearDown(self)
        shutil.rmtree('/tmp/minarca-test')
    
    def _add_user(self, username=None, email=None, password=None, user_root=None, is_admin=None):
        b = {}
        b['action'] = 'add'
        if username is not None:
            b['username'] = username
        if email is not None:
            b['email'] = email
        if password is not None:
            b['password'] = password
        if user_root is not None:
            b['user_root'] = user_root
        if is_admin is not None:
            b['is_admin'] = str(bool(is_admin)).lower()
        self.getPage("/admin/users/", method='POST', body=b)
    
    def test_add_user_without_user_root(self):
        """
        Add user without user_root
        
        Make sure the user_root getg populated with default value from basedir.
        """
        #  Add user to be listed
        self._add_user("mtest1", None, "mtest1", None, False)
        self.assertInBody("User added successfully.")
        user = self.app.userdb.get_user('mtest1')
        self.assertEquals('/tmp/minarca-test/mtest1', user.user_root)
    
    def test_add_user_with_user_root(self):
        """
        Add user with user_root
        
        Make sure the user_root get redefined inside basedir.
        """
        #  Add user to be listed
        self._add_user("mtest2", None, "mtest2", "/home/mtest2", False)
        self.assertInBody("User added successfully.")
        user = self.app.userdb.get_user('mtest2')
        self.assertEquals('/tmp/minarca-test/mtest2', user.user_root)
    

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
            'MinarcaUserBaseDir': '/tmp/minarca-test',
            })

    def setUp(self):
        self.app.userdb.get_user('admin').user_root = '/tmp'
        # Mock LDAP
        self.mockldap = MockLdap(self.directory)
        self.mockldap.start()
        self.ldapobj = self.mockldap['ldap://localhost/']
        WebCase.setUp(self)
        self.plugin = MinarcaUserSetup(self.app)
        if not os.path.isdir('/tmp/minarca-test'):
            os.mkdir('/tmp/minarca-test')

    def tearDown(self):
        WebCase.tearDown(self)
        # Stop patching ldap.initialize and reset state.
        self.mockldap.stop()
        del self.ldapobj
        del self.mockldap
        shutil.rmtree('/tmp/minarca-test')

    def test_login(self):
        """
        Check if new user is created with user_root and email.
        """
        userobj = self.app.userdb.login('bob', 'password')
        self.assertIsNotNone(userobj)
        self.assertTrue(self.app.userdb.exists('bob'))
        # Check if profile get update from Ldap info.
        self.assertEquals('bob@test.com', self.app.userdb.get_user('bob').email)
        self.assertEquals('/tmp/minarca-test/bob', self.app.userdb.get_user('bob').user_root)

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
        userobj = self.app.userdb.add_user('bob')
        with self.assertRaises(Exception):
            self.plugin.set_disk_quota(userobj, quota=1234567)

    @httpretty.activate
    def test_get_disk_usage(self):
        """
        Check if value is available.
        """
        # Checks if exception is raised when authentication is failing.
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/quota/bob",
                               body='{"avail": 2147483648, "used": 0, "size": 2147483648}')
        # Make sure an exception is raised.
        userobj = self.app.userdb.add_user('bob')
        self.assertEquals({"avail": 2147483648, "used": 0, "size": 2147483648}, self.plugin.get_disk_usage(userobj))
        
    def test_get_api_minarca(self):
        self._login('bob', 'password')
        self.getPage("/api/minarca")
        # Check version
        self.assertInBody('version')
        # Check remoteHost
        self.assertInBody('remotehost')
        self.assertInBody('127.0.0.1')
        # Check identity
        self.assertInBody('identity')

    def test_get_api_minarca_with_reverse_proxy(self):
        # When behind an apache reverse proxy, minarca server should make use
        # of the Header to determine the public hostname provided.
        self._login('bob', 'password')
        headers = [
            ('X-Forwarded-For', '10.255.1.106'),
            ('X-Forwarded-Host', 'sestican.patrikdufresne.com'),
            ('X-Forwarded-Server', '10.255.1.106')]

        self.getPage("/api/minarca", headers=headers)
        self.assertInBody('remotehost')
        self.assertInBody('sestican.patrikdufresne.com')


class MinarcaSshKeysTest(AppTestCase):
    """
    Collections of tests related to ssh keys file update.
    """
    USERNAME = 'admin'

    PASSWORD = 'test'
    
    base_dir = tempfile.mkdtemp(prefix='minarca_tests_')
    
    default_config = { 'MinarcaUserBaseDir': base_dir, }
    
    reset_testcases = True
    
    def setUp(self):
        AppTestCase.setUp(self)
        if not os.path.isdir(self.base_dir):
            os.mkdir(self.base_dir)
    
    def tearDown(self):
        shutil.rmtree(self.base_dir)
        AppTestCase.tearDown(self)
    
    def assertAuthorizedKeys(self, expected):
        filename = os.path.join(self.base_dir, '.ssh', 'authorized_keys')
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()
        self.assertEqual(data, expected)
    
    def test_update_authorized_keys(self):
        self.plugin = MinarcaUserSetup(self.app)
        self.plugin._update_authorized_keys()
    
    def test_add_key(self):
        # Read the key from a file
        filename = pkg_resources.resource_filename(__name__, 'test_publickey_ssh_rsa.pub')  # @UndefinedVariable
        with open(filename, 'r', encoding='utf8') as f: 
            key = f.readline()
        
        # Add the key to the user.
        userobj = self.app.userdb.add_user('testuser')
        userobj.add_authorizedkey(key)
        user_root = userobj.user_root
        
        # Validate
        self.assertAuthorizedKeys(
            '''command="/opt/minarca/bin/minarca-shell 'testuser' '%s'",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDDYeMPTCnRLFaLeSzsn++RD5jwuuez65GXrt9g7RYUqJka66cn7zHUhjDWx15fyEM3ikHGbmmWEP2csq11YCtvaTaz2GAnwcFNdt2NF0KGHMbE56Xq0eCkj1FCait/UyRBqkaFItYAoBdj4War9Xt+S5sV8qc5/TqTeku4Kg6ZBJRFCDHy6nR8Xf+tXiBrlfCnXvxamDI5kFP0B+npuBv+M4TjKFvwn5W8zYPPTEznilWnGvJFS71XwsOD/yHBGQb/Jz87aazNAeCznZRAJxfecJhgeChGZcGnXRAAdEeMbRyilYWaNquIpwrbNFElFlVf41EoDBk6woB8TeG0XFfz ikus060@ikus060-t530\n''' % user_root)
        
        # Update user's home
        user_root = os.path.join(self.base_dir, 'testing')
        userobj.user_root = user_root

        # Validate
        self.assertAuthorizedKeys(
            '''command="/opt/minarca/bin/minarca-shell 'testuser' '%s'",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDDYeMPTCnRLFaLeSzsn++RD5jwuuez65GXrt9g7RYUqJka66cn7zHUhjDWx15fyEM3ikHGbmmWEP2csq11YCtvaTaz2GAnwcFNdt2NF0KGHMbE56Xq0eCkj1FCait/UyRBqkaFItYAoBdj4War9Xt+S5sV8qc5/TqTeku4Kg6ZBJRFCDHy6nR8Xf+tXiBrlfCnXvxamDI5kFP0B+npuBv+M4TjKFvwn5W8zYPPTEznilWnGvJFS71XwsOD/yHBGQb/Jz87aazNAeCznZRAJxfecJhgeChGZcGnXRAAdEeMbRyilYWaNquIpwrbNFElFlVf41EoDBk6woB8TeG0XFfz ikus060@ikus060-t530\n''' % user_root)
        
        # Deleting the user should delete it's keys
        self.app.userdb.delete_user('testuser')
        
        # Validate
        self.assertAuthorizedKeys('')
    

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
