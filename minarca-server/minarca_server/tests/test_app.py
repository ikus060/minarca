# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import minarca_server.tests
import pkg_resources


class MinarcaApplicationTestWithHelpUrl(minarca_server.tests.AbstractMinarcaTest):

    default_config = {
        'minarca-help-url': 'https://example.com/help/'
    }

    def test_get_help(self):
        # Check if the URL can be changed
        self.getPage("/help")
        self.assertStatus(303)
        self.assertHeader('Location', 'https://example.com/help/')


class MinarcaApplicationTestWithRemoteIdentity(minarca_server.tests.AbstractMinarcaTest):

    login = True

    default_config = {
        'minarca-remote-host': "test.examples:2222",
        'minarca-remote-host-identity': pkg_resources.resource_filename(__name__, '')
    }

    def test_get_api_minarca_identity(self):
        data = self.getJson("/api/minarca/")
        self.assertIn("[test.examples]:2222", data['identity'])
