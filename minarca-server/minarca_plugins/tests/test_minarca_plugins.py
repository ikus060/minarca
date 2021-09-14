#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
"""
Created on Jan 23, 2016

@author: Patrik Dufresne <patrik@ikus-soft.com>
"""

import grp
from io import open
import logging
import os
import pwd
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock

import httpretty
import pkg_resources
from rdiffweb.core.store import ADMIN_ROLE
import rdiffweb.test

from minarca_plugins import MinarcaUserSetup, MinarcaQuota
import minarca_plugins


class AbstractMinarcaTest(rdiffweb.test.WebCase):
    """
    Abstract test class to setup minarca for testing.
    """

    @classmethod
    def setup_class(cls):
        if cls is AbstractMinarcaTest:
            raise unittest.SkipTest(
                "%s is an abstract base class" % cls.__name__)
        if not os.path.isdir('/tmp/minarca-test'):
            os.mkdir('/tmp/minarca-test')
        # Use temporary folder for base dir
        cls.default_config['MinarcaUserBaseDir'] = '/tmp/minarca-test'
        tempfile.tempdir = '/tmp/minarca-test'
        # Use current user for owner and group
        cls.default_config['MinarcaUserDirOwner'] = pwd.getpwuid(os.getuid())[
            0]
        cls.default_config['MinarcaUserDirGroup'] = pwd.getpwuid(os.getuid())[
            0]
        super(AbstractMinarcaTest, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(AbstractMinarcaTest, cls).teardown_class()
        shutil.rmtree('/tmp/minarca-test', ignore_errors=True)
        tempfile.tempdir = None


class MinarcaUserSetupTest(AbstractMinarcaTest):

    login = True

    @classmethod
    def setup_class(cls):
        super(MinarcaUserSetupTest, cls).setup_class()

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
            b['role'] = str(ADMIN_ROLE)
        self.getPage("/admin/users/", method='POST', body=b)

    def test_add_user_without_user_root(self):
        """
        Add user without user_root

        Make sure the user_root getg populated with default value from basedir.
        """
        # Check if minarca base dir is properly defined
        self.assertEqual('/tmp/minarca-test',
                         self.app.cfg.minarca_user_base_dir)

        #  Add user to be listed
        self._add_user("mtest1", None, "mtest1", None, False)
        self.assertInBody("User added successfully.")
        user = self.app.store.get_user('mtest1')
        self.assertEqual('/tmp/minarca-test/mtest1', user.user_root)

    def test_add_user_with_user_root(self):
        """
        Add user with user_root

        Make sure the user_root get redefined inside basedir.
        """
        #  Add user to be listed
        self._add_user("mtest2", None, "mtest2", "/home/mtest2", False)
        self.assertInBody("User added successfully.")
        user = self.app.store.get_user('mtest2')
        self.assertEqual('/tmp/minarca-test/mtest2', user.user_root)

    def test_default_arguments(self):
        self.assertEqual("blue", self.app.cfg.default_theme)
        self.assertIn("minarca.ico", self.app.cfg.favicon)
        self.assertEqual("Minarca", self.app.cfg.footer_name)
        self.assertEqual("Minarca", self.app.cfg.header_name)
        self.assertIn("minarca_22.png", self.app.cfg.header_logo)
        self.assertEqual("/var/log/minarca/access.log",
                         self.app.cfg.log_access_file)
        self.assertEqual("/var/log/minarca/server.log", self.app.cfg.log_file)
        self.assertIn('minarca', self.app.cfg.welcome_msg[''])
        self.assertIn('minarca', self.app.cfg.welcome_msg['fr'])


class MinarcaRemoteIdentityTest(AbstractMinarcaTest):

    default_config = {
        'minarcaremotehost': "test.examples:2222",
        # @UndefinedVariable
        'minarcaremotehostidentity': pkg_resources.resource_filename(__name__, '')
    }

    def test_get_api_minarca_identity(self):
        self._login(self.USERNAME, self.PASSWORD)
        data = self.getJson("/api/minarca/")
        self.assertIn("[test.examples]:2222", data['identity'])


class MinarcaRemoteIdentityNoneTest(AbstractMinarcaTest):

    login = True

    def test_get_api_minarca(self):
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
        headers = [
            ('X-Forwarded-For', '10.255.1.106'),
            ('X-Forwarded-Host', 'sestican.patrikdufresne.com'),
            ('X-Forwarded-Server', '10.255.1.106')]

        self.getPage("/api/minarca", headers=headers)
        self.assertInBody('remotehost')
        self.assertInBody('sestican.patrikdufresne.com')


class MinarcaHelpTest(AbstractMinarcaTest):

    default_config = {
        'minarcahelpurl': 'https://example.com/help/'
    }

    def test_get_help(self):
        # Check if the URL can be changed
        self.getPage("/help")
        self.assertStatus(303)
        self.assertHeader('Location', 'https://example.com/help/')


class MinarcaAdminLogView(AbstractMinarcaTest):

    default_config = {
        'logfile': '/tmp/minarca-test/server.log',
        'minarcaquotaapiurl': 'http://localhost:8081',
    }

    login = True

    @classmethod
    def setup_class(cls):
        super(MinarcaAdminLogView, cls).setup_class()
        with open('/tmp/minarca-test/server.log', 'w') as f:
            f.write('data')
        with open('/tmp/minarca-test/shell.log', 'w') as f:
            f.write('data')
        with open('/tmp/minarca-test/quota-api.log', 'w') as f:
            f.write('data')

    def test_adminview(self):
        self.getPage('/admin/logs')
        self.assertStatus(200)
        self.assertInBody('server.log', 'server log should be in admin view')
        self.assertInBody(
            'shell.log', 'minarca-shell log should be in admin view')
        self.assertInBody(
            'quota-api.log', 'minarca-quota-api log should be in admin view')
        self.assertNotInBody('Error getting file content')


class MinarcaUserQuota(rdiffweb.test.AppTestCase):
    """
    Test Get/Set user quota
    """

    default_config = {
        'minarcaquotaapiurl': 'http://minarca:secret@localhost:8081/',
        'minarcauserbasedir': '/tmp/minarca-test'
    }

    def setUp(self):
        # Create folder
        if not os.path.isdir('/tmp/minarca-test'):
            os.mkdir('/tmp/minarca-test')
        tempfile.tempdir = '/tmp/minarca-test'
        # Setup app
        super().setUp()
        # Start the plugin.
        self.plugin = MinarcaQuota(self.app)

    def tearDown(self):
        super().tearDown()
        # Remove folder
        shutil.rmtree('/tmp/minarca-test')
        tempfile.tempdir = None

    @httpretty.activate
    def test_set_disk_quota(self):
        userobj = self.app.store.add_user('bob')
        httpretty.register_uri(httpretty.POST, "http://localhost:8081/quota/" + str(userobj.userid),
                               body='{"avail": 2147483648, "used": 0, "size": 2147483648}')
        # Mock call to chattr because it might fail on filesystem not supporting projectid.
        minarca_plugins.subprocess.check_output = MagicMock()
        # Set quota
        self.plugin.set_disk_quota(userobj, quota=1234567)
        # Check if subprocessis called twice
        self.assertEqual(2, minarca_plugins.subprocess.check_output.call_count,
                         "subprocess.check_output should be called")

    @httpretty.activate
    def test_update_userquota_401(self):
        userobj = self.app.store.add_user('bob')
        # Checks if exception is raised when authentication is failing.
        httpretty.register_uri(httpretty.POST, "http://localhost:8081/quota/" + str(userobj.userid),
                               status=401)
        # Make sure an exception is raised.
        with self.assertRaises(Exception):
            self.plugin.set_disk_quota(userobj, quota=1234567)

    @httpretty.activate
    def test_get_disk_usage(self):
        """
        Check if value is available.
        """
        # Make sure an exception is raised.
        userobj = self.app.store.add_user('bob')
        # Checks if exception is raised when authentication is failing.
        httpretty.register_uri(httpretty.GET, "http://localhost:8081/quota/" + str(userobj.userid),
                               body='{"used": 1234, "size": 2147483648}')
        self.assertEqual(1234, self.plugin.get_disk_usage(userobj))


class MinarcaSshKeysTest(rdiffweb.test.AppTestCase):
    """
    Collections of tests related to ssh keys file update.
    """
    base_dir = tempfile.mkdtemp(prefix='minarca_tests_')

    default_config = {
        'MinarcaUserBaseDir': base_dir,
        'MinarcaUserDirOwner': pwd.getpwuid(os.getuid()).pw_name,
        'MinarcaUserDirGroup': grp.getgrgid(os.getgid()).gr_name,
    }

    reset_testcases = True

    def setUp(self):
        if not os.path.isdir(self.base_dir):
            os.mkdir(self.base_dir)
        tempfile.tempdir = self.base_dir
        super().setUp()

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.base_dir)
        tempfile.tempdir = None

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
        filename = pkg_resources.resource_filename(
            __name__, 'test_publickey_ssh_rsa.pub')  # @UndefinedVariable
        with open(filename, 'r', encoding='utf8') as f:
            key = f.readline()

        # Add the key to the user.
        userobj = self.app.store.add_user('testuser')
        userobj.add_authorizedkey(key)
        user_root = userobj.user_root

        # Validate
        self.assertAuthorizedKeys(
            '''command="export MINARCA_USERNAME='testuser' MINARCA_USER_ROOT='%s';/opt/minarca-server/bin/minarca-shell",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDDYeMPTCnRLFaLeSzsn++RD5jwuuez65GXrt9g7RYUqJka66cn7zHUhjDWx15fyEM3ikHGbmmWEP2csq11YCtvaTaz2GAnwcFNdt2NF0KGHMbE56Xq0eCkj1FCait/UyRBqkaFItYAoBdj4War9Xt+S5sV8qc5/TqTeku4Kg6ZBJRFCDHy6nR8Xf+tXiBrlfCnXvxamDI5kFP0B+npuBv+M4TjKFvwn5W8zYPPTEznilWnGvJFS71XwsOD/yHBGQb/Jz87aazNAeCznZRAJxfecJhgeChGZcGnXRAAdEeMbRyilYWaNquIpwrbNFElFlVf41EoDBk6woB8TeG0XFfz ikus060@ikus060-t530\n''' % user_root)

        # Update user's home
        user_root = os.path.join(self.base_dir, 'testing')
        userobj.user_root = user_root

        # Validate
        self.assertAuthorizedKeys(
            '''command="export MINARCA_USERNAME='testuser' MINARCA_USER_ROOT='%s';/opt/minarca-server/bin/minarca-shell",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDDYeMPTCnRLFaLeSzsn++RD5jwuuez65GXrt9g7RYUqJka66cn7zHUhjDWx15fyEM3ikHGbmmWEP2csq11YCtvaTaz2GAnwcFNdt2NF0KGHMbE56Xq0eCkj1FCait/UyRBqkaFItYAoBdj4War9Xt+S5sV8qc5/TqTeku4Kg6ZBJRFCDHy6nR8Xf+tXiBrlfCnXvxamDI5kFP0B+npuBv+M4TjKFvwn5W8zYPPTEznilWnGvJFS71XwsOD/yHBGQb/Jz87aazNAeCznZRAJxfecJhgeChGZcGnXRAAdEeMbRyilYWaNquIpwrbNFElFlVf41EoDBk6woB8TeG0XFfz ikus060@ikus060-t530\n''' % user_root)

        # Deleting the user should delete it's keys
        userobj.delete()

        # Validate
        self.assertAuthorizedKeys('')


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
