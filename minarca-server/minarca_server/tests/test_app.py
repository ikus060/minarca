# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
from base64 import b64encode

import pkg_resources
from rdiffweb.core.model import UserObject

import minarca_server.tests


class MinarcaApplicationTestWithHelpUrl(minarca_server.tests.AbstractMinarcaTest):
    default_config = {'minarca-help-url': 'https://example.com/help/'}

    def test_get_help(self):
        # Check if the URL can be changed
        self.getPage("/help")
        self.assertStatus(303)
        self.assertHeader('Location', 'https://example.com/help/')


class MinarcaApplicationTestWithRemoteIdentity(minarca_server.tests.AbstractMinarcaTest):
    basic_headers = [("Authorization", "Basic " + b64encode(b"admin:admin123").decode('ascii'))]

    default_config = {
        'minarca-remote-host': "test.examples:2222",
        'minarca-remote-host-identity': pkg_resources.resource_filename(__name__, ''),
    }

    def test_get_api_minarca_identity(self):
        data = self.getJson("/api/minarca/", headers=self.basic_headers)
        self.assertIn("[test.examples]:2222", data['identity'])

    def test_get_bg_jpg(self):
        self.getPage("/static/bg.jpg")
        self.assertStatus(200)


class MinarcaApplicationTestPageAdminUsers(minarca_server.tests.AbstractMinarcaTest):
    login = True

    def test_create_new_user(self):
        # Given an administrator authenticated
        # When creating a new user in Minarca
        self.getPage(
            "/admin/users/",
            method="POST",
            body={
                'action': 'add',
                'username': 'patrik',
                'fullname': 'Patrik Dufresne',
                'password': 'this is my long password',
                'user_root': '',
            },
        )
        self.assertStatus(200)
        # Then user get added in database
        userobj = UserObject.get_user('patrik')
        self.assertEqual(self.base_dir + '/patrik', userobj.user_root)
        # Then no error are displayed to the user
        self.assertNotInBody('alert-danger')
        # Then succes message is displayed
        self.assertInBody('User added successfully.')
