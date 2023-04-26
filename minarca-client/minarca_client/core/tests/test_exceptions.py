# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Nov. 12, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''

import sys
import unittest

import rdiff_backup.connection

from minarca_client.core.exceptions import SshConnectionError, raise_exception


class TestExceptions(unittest.TestCase):
    def test_create_exception(self):
        # Given an exception raise by rdiffweb backup
        try:
            try:
                raise rdiff_backup.connection.ConnectionReadError(
                    'Truncated header string (problem probably originated remotely)'
                )
            except Exception:
                sys.exit(1)
        except SystemExit as e:
            # When raising it as a custom exception
            # Then it return an SSHConnectionErro
            with self.assertRaises(SshConnectionError):
                raise_exception(e)
