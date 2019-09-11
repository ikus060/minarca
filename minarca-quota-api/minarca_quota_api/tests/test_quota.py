#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca Quota API
#
# Copyright (C) 2019 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
"""
Created on Mar 7, 2018

@author: Patrik Dufresne
"""

from __future__ import unicode_literals

from base64 import b64encode
import cherrypy
from cherrypy.test import helper
from collections import namedtuple
from future.backports.urllib.parse import urlencode
from mock import MagicMock
import unittest

import minarca_quota_api


class TestQuota(helper.CPWebCase):  # @UndefinedVariable

    def setup_server():
        cherrypy.tree.mount(minarca_quota_api.Root())

    setup_server = staticmethod(setup_server)

    interactive = False

    def test_get_quota(self):
        # Mock the command line call
        minarca_quota_api.subprocess.check_output = MagicMock(return_value='1122091872\n718078912672\n2147483648\n')

        # Make the query
        headers = [("Authorization", "Basic " + b64encode(b"minarca:secret").decode('ascii'))]
        self.getPage('/quota/someuser', headers=headers)
        self.assertStatus(200)
        pass

    def test_set_quota(self):
        # Mock the command line call
        minarca_quota_api.subprocess.check_output = MagicMock(side_effect=["cannot create 'tank/someuser': dataset already exists", '', '1122091872\n718078912672\n2147483648\n'])

        # Make the query
        headers = [("Authorization", "Basic " + b64encode(b"minarca:secret").decode('ascii'))]
        body = urlencode([(b'size', b'2147483648')])
        self.getPage('/quota/someuser', method='PUT', headers=headers, body=body)
        self.assertStatus(200)
        pass

    def test_set_quota_invalid_user(self):

        # Make the query
        headers = [("Authorization", "Basic " + b64encode(b"minarca:secret").decode('ascii'))]
        body = urlencode([(b'size', b'2147483648')])
        self.getPage('/quota/someuser', method='PUT', headers=headers, body=body)
        self.assertStatus(500)
        pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
