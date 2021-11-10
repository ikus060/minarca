# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Oct. 22, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''

import unittest
from unittest.mock import MagicMock

import responses
from minarca_client.core.latest import LATEST_VERSION_URL, LatestCheck, LatestCheckFailed


class LatestCheckTest(unittest.TestCase):

    @responses.activate
    def test_get_version_info(self):
        # Given a web server with the latest information
        responses.add(responses.GET, LATEST_VERSION_URL, body='1.2.3')
        # When querying the latest information
        latest = LatestCheck()
        latest_info = latest.get_latest_version()
        # Then the information is fetch from web server and return in python format.
        self.assertEqual('1.2.3', latest_info)

    @responses.activate
    def test_is_latest_with_invalid_data(self):
        # Given a web server with the latest information
        responses.add(responses.GET, LATEST_VERSION_URL, body='this is some invalid error.')
        # When querying the latest information
        latest = LatestCheck()
        with self.assertRaises(LatestCheckFailed):
            latest.is_latest()

    @responses.activate
    @responses.activate
    def test_is_latest_with_same_version(self):
        # Given latest version 1.2.3
        responses.add(responses.GET, LATEST_VERSION_URL, body='1.2.3')
        # Given current version 1.2.3
        latest = LatestCheck()
        latest.get_current_version = MagicMock(return_value='1.2.3')
        # When checking if latest version
        # Then it's the latest version.
        self.assertTrue(latest.is_latest())

    @responses.activate
    def test_is_latest_with_old_version(self):
        # Given latest version 1.2.3
        responses.add(responses.GET, LATEST_VERSION_URL, body='1.2.3')
        # Given current version is older
        latest = LatestCheck()
        latest.get_current_version = MagicMock(return_value='1.0.0')
        # When checking if latest version
        # Then it's the NOT latest version.
        self.assertFalse(latest.is_latest())

    @responses.activate
    def test_is_latest_with_new_version(self):
        # Given latest version 1.2.3
        responses.add(responses.GET, LATEST_VERSION_URL, body='1.2.3')
        # Given current version is older
        latest = LatestCheck()
        latest.get_current_version = MagicMock(return_value='1.2.3')
        # When checking if latest version
        # Then it's the NOT latest version.
        self.assertTrue(latest.is_latest())

    @responses.activate
    def test_is_latest_with_dev_version(self):
        # Given latest version 1.2.3
        responses.add(responses.GET, LATEST_VERSION_URL, body='1.2.3')
        # Given current version is older
        latest = LatestCheck()
        latest.get_current_version = MagicMock(return_value='DEV')
        # When checking if latest version
        # Then it's the NOT latest version.
        self.assertTrue(latest.is_latest())
