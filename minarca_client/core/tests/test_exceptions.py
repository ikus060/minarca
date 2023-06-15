# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Nov. 12, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''


import unittest

from parameterized import parameterized

from minarca_client.core.exceptions import (
    CaptureException,
    ConnectException,
    DiskFullError,
    DiskQuotaExceededError,
    PermissionDeniedError,
    UnknownHostException,
    UnknownHostKeyError,
)


class TestExceptions(unittest.TestCase):
    @parameterized.expand(
        [
            ('ssh: connect to host test.minarca.net port 8976: Connection refused', ConnectException),
            ('ssh: Could not resolve hostname', UnknownHostException),
            ('Host key verification failed.', UnknownHostKeyError),
            ('Permission denied (publickey)', PermissionDeniedError),
            ('OSError: [Errno 122] Disk quota exceeded', DiskQuotaExceededError),
            ('OSError: [Errno 28] No space left on device', DiskFullError),
            ('Other', None),
        ]
    )
    def test_capture_exception(self, line, expected_error):
        capture = CaptureException()
        capture.parse(line)
        if expected_error:
            self.assertIsInstance(capture.exception, expected_error)
        else:
            self.assertIsNone(capture.exception)
