#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca Quota API
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
"""
Created on Mar 7, 2018

@author: Patrik Dufresne <patrik@ikus-soft.com>
"""

from base64 import b64encode
from urllib.parse import urlencode

import cherrypy
from cherrypy.test import helper
from unittest.mock import MagicMock

import minarca_quota_api
from minarca_quota_api.zfs_quota import ZFSQuotaException


class TestQuota(helper.CPWebCase):  # @UndefinedVariable

    def setup_server():
        cherrypy.tree.mount(minarca_quota_api.Root(pool='rpool/minarca'))

    setup_server = staticmethod(setup_server)

    interactive = False

    def test_gc(self):
        pass

    def test_get_index(self):
        self.getPage('/')
        self.assertStatus(200)
        self.assertBody("Minarca Quota API")

    def test_get_quota(self):
        # Mock the command line call
        minarca_quota_api.get_quota = MagicMock(return_value={"size": 654, "used": 123})

        # Make the query
        headers = [("Authorization", "Basic " + b64encode(b"minarca:secret").decode('ascii'))]
        self.getPage('/quota/123', headers=headers)
        self.assertStatus(200)

    def test_get_quota_with_invalid_name(self):
        # Make the query
        headers = [("Authorization", "Basic " + b64encode(b"minarca:secret").decode('ascii'))]
        self.getPage('/quota/someuser', headers=headers)
        self.assertStatus(400)
        self.assertInBody("invalid uid: someuser")

    def test_set_quota(self):
        # Mock the command line call
        minarca_quota_api.get_quota = MagicMock(return_value={"size": 2147483648, "used": 1121784464})
        minarca_quota_api.set_quota = MagicMock()

        # Make the query
        headers = [("Authorization", "Basic " + b64encode(b"minarca:secret").decode('ascii'))]
        body = urlencode([(b'size', b'2147483648')])
        self.getPage('/quota/123', method='PUT', headers=headers, body=body)
        self.assertStatus(200)

    def test_set_quota_raise_error(self):
        # Mock the command line call
        minarca_quota_api.get_quota = MagicMock(return_value={"size": 2147483648, "used": 1121784464})
        minarca_quota_api.set_quota = MagicMock(side_effect=ZFSQuotaException('this is a error message'))

        # Make the query
        headers = [("Authorization", "Basic " + b64encode(b"minarca:secret").decode('ascii'))]
        body = urlencode([(b'size', b'2147483648')])
        self.getPage('/quota/123', method='PUT', headers=headers, body=body)
        # Make sure to return HTTP error 500 when exception occur.
        self.assertStatus(500)
        # Check if the error message is in the body
        self.assertInBody("this is a error message")

    def test_set_quota_with_invalid_size(self):
        # Make the query
        headers = [("Authorization", "Basic " + b64encode(b"minarca:secret").decode('ascii'))]
        body = urlencode([(b'size', b'foo')])
        self.getPage('/quota/123', method='PUT', headers=headers, body=body)
        # Make sure to return HTTP error 500 when exception occur.
        self.assertStatus(400)
        # Check if the error message is in the body
        self.assertInBody("invalid size: foo")
