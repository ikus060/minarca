# Copyright (C) 2025 IKUS Software. All rights reserved.
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
    JailCreationError,
    PermissionDeniedError,
    RemoteServerTruncatedHeader,
    UnknownHostException,
    UnknownHostKeyError,
)


class TestExceptions(unittest.TestCase):
    @parameterized.expand(
        [
            (b'ssh: connect to host test.minarca.net port 8976: Connection refused', ConnectException),
            (b'ssh: Could not resolve hostname', UnknownHostException),
            (b'Host key verification failed.', UnknownHostKeyError),
            (b'Permission denied (publickey)', PermissionDeniedError),
            (b'OSError: [Errno 122] Disk quota exceeded', DiskQuotaExceededError),
            (b'OSError: [Errno 28] No space left on device', DiskFullError),
            (
                b"due to exception 'Truncated header <b''> (problem probably originated remotely)'.",
                RemoteServerTruncatedHeader,
            ),
            (b'ERROR: fail to create rdiff-backup jail', JailCreationError),
            (b'Other', None),
        ]
    )
    def test_capture_exception(self, line, expected_error):
        capture = CaptureException()
        capture.parse(line)
        if expected_error:
            self.assertIsInstance(capture.exception, expected_error)
        else:
            self.assertIsNone(capture.exception)
