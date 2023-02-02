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
import os
import pwd
import time
import unittest
from base64 import b64encode
from io import open
from unittest.mock import ANY

import cherrypy
import pkg_resources
import responses
from rdiffweb.core.model import SshKey, UserObject

import minarca_server
import minarca_server.tests


class MinarcaPluginTest(minarca_server.tests.AbstractMinarcaTest):
    basic_headers = [("Authorization", "Basic " + b64encode(b"admin:admin123").decode('ascii'))]

    login = True

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
            b['role'] = str(UserObject.ADMIN_ROLE)
        self.getPage("/admin/users/", method='POST', body=b)

    def test_add_user_without_user_root(self):
        # Given a minarca base dir
        self.assertIsNotNone(self.app.cfg.minarca_user_base_dir)
        # When adding a new user without specific user_root
        self._add_user("mtest1", None, "pr3j5Dwi", None, False)
        self.assertStatus(200)
        self.assertInBody("User added successfully.")
        # Then user root directory is defined within the base dir
        user = UserObject.get_user('mtest1')
        self.assertEqual(os.path.join(self.base_dir, 'mtest1'), user.user_root)

    def test_add_user_with_user_root(self):
        # Given a minarca base dir
        self.assertIsNotNone(self.app.cfg.minarca_user_base_dir)
        # When adding a new user with a specific user_root
        self._add_user("mtest2", None, "pr3j5Dwi", "/home/mtest2", False)
        self.assertStatus(200)
        self.assertInBody("User added successfully.")
        # Then user root is updated to be within the base dir
        user = UserObject.get_user('mtest2')
        self.assertEqual(os.path.join(self.base_dir, 'mtest2'), user.user_root)

    def test_default_config(self):
        self.assertEqual("default", self.app.cfg.default_theme)
        self.assertIn("minarca.ico", self.app.cfg.favicon)
        self.assertEqual("Minarca", self.app.cfg.footer_name)
        self.assertEqual("Minarca", self.app.cfg.header_name)
        self.assertIn("minarca_logo.png", self.app.cfg.header_logo)
        self.assertIn("logo.png", self.app.cfg.logo)
        self.assertEqual("/var/log/minarca/access.log", self.app.cfg.log_access_file)
        # log_file get overriden by testcase. So dont validate it.
        self.assertIsNotNone(self.app.cfg.log_file)
        self.assertIn('minarca', self.app.cfg.welcome_msg[''])
        self.assertIn('minarca', self.app.cfg.welcome_msg['fr'])

    def test_get_api_minarca(self):
        self.getPage("/api/minarca", headers=self.basic_headers)
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
            ('Host', 'sestican.patrikdufresne.com'),
            ('X-Forwarded-For', '10.255.1.106'),
            ('X-Forwarded-Host', 'junk.patrikdufresne.com'),
            ('X-Forwarded-Server', '10.255.1.106'),
        ]

        self.getPage("/api/minarca", headers=self.basic_headers + headers)
        self.assertInBody('remotehost')
        self.assertInBody('sestican.patrikdufresne.com')

    def test_get_location(self):
        """
        Given an empty minarca_quota_api_url
        When location page get request
        Then the disk usage is repported using the default behaviour.
        """
        # Make sure disk usage fall back to default behaviour.
        self.getPage('/')
        self.assertStatus(200)
        self.assertInBody('Usage')

    def test_get_disk_usage(self):
        # Given an empty minarca_quota_api_url
        # When disk usage get requested
        userobj = UserObject.add_user('bob')
        userobj.commit()
        # Then the disk usage is repported using the default behaviour.
        self.assertIsNotNone(userobj.disk_quota)
        self.assertIsNotNone(userobj.disk_usage)

    def test_set_disk_quota(self):
        # Given an empty minarca_quota_api_url
        # When trying to set disk quota
        userobj = UserObject.add_user('bob')
        # Then setting disk_quota does nothing
        userobj.disk_quota = 12345
        userobj.commit()


class MinarcaAdminLogView(minarca_server.tests.AbstractMinarcaTest):
    default_config = {
        'minarca-quota-api-url': 'http://localhost:8081',
    }

    login = True

    @classmethod
    def setup_class(cls):
        super().setup_class()
        with open(os.path.join(cls.base_dir, 'server.log'), 'w') as f:
            f.write(
                '[2022-11-15 04:58:41,056][INFO   ][112.4.177.132][admin][CP Server Thread-4][activity] adding new user [oro]\n'
            )
        with open(os.path.join(cls.base_dir, 'shell.log'), 'w') as f:
            f.write(
                '[2023-02-15 13:36:34,494][INFO   ][192.222.177.77][mike][MainThread][minarca_server.shell] running command [/usr/bin/rdiff-backup-2.0 --server] in jail [/backups/mike]\n'
            )

    def test_admin_logs(self):
        # Given server, shell and quota logs file
        # When querying the system logs
        self.getPage('/admin/logs/')
        # Then page return without error
        self.assertStatus(200)
        # When querying system logs data
        data = self.getJson('/admin/logs/data.json')
        # Then is contains our logs.
        self.assertEqual(
            data['data'],
            [
                [
                    'server.log',
                    ANY,
                    '112.4.177.132',
                    'admin',
                    'INFO adding new user [oro]',
                    'activity',
                ],
                [
                    'shell.log',
                    ANY,
                    '192.222.177.77',
                    'mike',
                    'INFO running command [/usr/bin/rdiff-backup-2.0 --server] in jail [/backups/mike]',
                    None,
                ],
            ],
        )


class MinarcaPluginTestWithQuotaAPI(minarca_server.tests.AbstractMinarcaTest):
    default_config = {
        'minarca-quota-api-url': 'http://minarca:secret@localhost:8081/',
    }

    @responses.activate
    @unittest.mock.patch('minarca_server.plugins.minarca.subprocess.check_output')
    def test_set_disk_quota(self, mock_check_output):
        # Given a valid use from database
        userobj = UserObject.add_user('bob')
        userobj.commit()
        # Given a mock quota-api
        responses.add(
            responses.POST,
            "http://minarca:secret@localhost:8081/quota/" + str(userobj.userid),
            json={"avail": 2147483648, "used": 0, "size": 2147483648},
        )
        # When setting a new user quota
        quota = cherrypy.engine.publish('set_disk_quota', userobj, quota=1234567)
        self.assertEqual([1234567], quota)
        # Then webservice was called
        self.assertEqual(1, len(responses.calls))
        # Then wait for the task to be scheduled
        time.sleep(2)
        # Then subprocess get called twice
        self.assertEqual(1, mock_check_output.call_count, "subprocess.check_output should be called")
        mock_check_output.assert_any_call(['/usr/bin/chattr', '-R', '+P', '-p', str(userobj.userid), ANY], stderr=-2)

    @responses.activate
    def test_update_userquota_401(self):
        userobj = UserObject.add_user('bob')
        userobj.commit()
        # Checks if exception is raised when authentication is failing.
        responses.add(responses.POST, "http://minarca:secret@localhost:8081/quota/" + str(userobj.userid), status=401)
        # Make sure an exception is raised.
        quota = cherrypy.engine.publish('set_disk_quota', userobj, quota=1234567)
        self.assertEqual([0], quota)

    @responses.activate
    def test_get_disk_quota(self):
        """
        Check if value is available.
        """
        # Make sure an exception is raised.
        userobj = UserObject.add_user('bob')
        userobj.commit()
        # Checks if exception is raised when authentication is failing.
        responses.add(
            responses.GET,
            "http://minarca:secret@localhost:8081/quota/" + str(userobj.userid),
            body='{"used": 1234, "size": 2147483648}',
        )
        # When querying the disk quota
        quota = cherrypy.engine.publish('get_disk_quota', userobj)
        # Then the quota is returned
        self.assertEqual([2147483648], quota)

    @responses.activate
    def test_get_disk_usage(self):
        """
        Check if value is available.
        """
        # Make sure an exception is raised.
        userobj = UserObject.add_user('bob')
        userobj.commit()
        # Checks if exception is raised when authentication is failing.
        responses.add(
            responses.GET,
            "http://minarca:secret@localhost:8081/quota/" + str(userobj.userid),
            body='{"used": 1234, "size": 2147483648}',
        )
        # When querying the disk quota
        quota = cherrypy.engine.publish('get_disk_usage', userobj)
        # Then the quota is returned
        self.assertEqual([1234], quota)


class MinarcaPluginTestWithOwnerAndGroup(minarca_server.tests.AbstractMinarcaTest):
    default_config = {
        'MinarcaUserDirOwner': pwd.getpwuid(os.getuid()).pw_name,
        'MinarcaUserDirGroup': grp.getgrgid(os.getgid()).gr_name,
    }

    def _read_ssh_key(self, filename):
        filename = pkg_resources.resource_filename(__name__, filename)
        with open(filename, 'r', encoding='utf8') as f:
            return f.readline()

    def assertAuthorizedKeys(self, expected):
        filename = os.path.join(self.base_dir, '.ssh', 'authorized_keys')
        with open(filename, 'r', encoding='utf-8') as f:
            data = f.read()
        self.assertEqual(data, expected)

    def test_update_authorized_keys(self):
        cherrypy.minarca._update_authorized_keys()

    def test_add_key(self):
        # Given all the keys are drop
        SshKey.query.delete()
        SshKey.session.commit()

        # Read the key from a file
        key = self._read_ssh_key('test_publickey_ssh_rsa.pub')

        # Add the key to the user.
        userobj = UserObject.add_user('testuser')
        userobj.commit()
        userobj.add_authorizedkey(key)
        userobj.commit()
        user_root = userobj.user_root

        # Validate
        self.assertAuthorizedKeys(
            '''command="export MINARCA_USERNAME='testuser' MINARCA_USER_ROOT='%s';/opt/minarca-server/bin/minarca-shell",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDDYeMPTCnRLFaLeSzsn++RD5jwuuez65GXrt9g7RYUqJka66cn7zHUhjDWx15fyEM3ikHGbmmWEP2csq11YCtvaTaz2GAnwcFNdt2NF0KGHMbE56Xq0eCkj1FCait/UyRBqkaFItYAoBdj4War9Xt+S5sV8qc5/TqTeku4Kg6ZBJRFCDHy6nR8Xf+tXiBrlfCnXvxamDI5kFP0B+npuBv+M4TjKFvwn5W8zYPPTEznilWnGvJFS71XwsOD/yHBGQb/Jz87aazNAeCznZRAJxfecJhgeChGZcGnXRAAdEeMbRyilYWaNquIpwrbNFElFlVf41EoDBk6woB8TeG0XFfz ikus060@ikus060-t530\n'''
            % user_root
        )

        # Update user's home
        user_root = os.path.join(self.base_dir, 'testing')
        userobj.user_root = user_root
        userobj.commit()

        # Validate
        self.assertAuthorizedKeys(
            '''command="export MINARCA_USERNAME='testuser' MINARCA_USER_ROOT='%s';/opt/minarca-server/bin/minarca-shell",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDDYeMPTCnRLFaLeSzsn++RD5jwuuez65GXrt9g7RYUqJka66cn7zHUhjDWx15fyEM3ikHGbmmWEP2csq11YCtvaTaz2GAnwcFNdt2NF0KGHMbE56Xq0eCkj1FCait/UyRBqkaFItYAoBdj4War9Xt+S5sV8qc5/TqTeku4Kg6ZBJRFCDHy6nR8Xf+tXiBrlfCnXvxamDI5kFP0B+npuBv+M4TjKFvwn5W8zYPPTEznilWnGvJFS71XwsOD/yHBGQb/Jz87aazNAeCznZRAJxfecJhgeChGZcGnXRAAdEeMbRyilYWaNquIpwrbNFElFlVf41EoDBk6woB8TeG0XFfz ikus060@ikus060-t530\n'''
            % user_root
        )

        # Deleting the user should delete it's keys
        userobj.delete()
        userobj.commit()

        # Validate
        self.assertAuthorizedKeys('')

    def test_add_key_with_rogue_name(self):
        # Given an SSH Key
        key = self._read_ssh_key('test_publickey_ssh_rsa.pub')

        # When adding an SSH Key with a newline
        userobj = UserObject.add_user('testuser')
        userobj.commit()
        userobj.add_authorizedkey(key, comment='comment\nrogue data')
        userobj.commit()

        # Then the new line get replace by space
        self.assertAuthorizedKeys(
            '''command="export MINARCA_USERNAME='testuser' MINARCA_USER_ROOT='%s';/opt/minarca-server/bin/minarca-shell",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDDYeMPTCnRLFaLeSzsn++RD5jwuuez65GXrt9g7RYUqJka66cn7zHUhjDWx15fyEM3ikHGbmmWEP2csq11YCtvaTaz2GAnwcFNdt2NF0KGHMbE56Xq0eCkj1FCait/UyRBqkaFItYAoBdj4War9Xt+S5sV8qc5/TqTeku4Kg6ZBJRFCDHy6nR8Xf+tXiBrlfCnXvxamDI5kFP0B+npuBv+M4TjKFvwn5W8zYPPTEznilWnGvJFS71XwsOD/yHBGQb/Jz87aazNAeCznZRAJxfecJhgeChGZcGnXRAAdEeMbRyilYWaNquIpwrbNFElFlVf41EoDBk6woB8TeG0XFfz comment rogue data\n'''
            % userobj.user_root
        )
