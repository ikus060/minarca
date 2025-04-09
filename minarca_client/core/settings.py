# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Oct 21, 2024

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import ast
import os

from minarca_client.core.config import Datetime, KeyValueConfigFile


def _bool(x):
    if isinstance(x, bool):
        return x
    return str(x).lower() in [True, 'true', 'yes', '1']


def list_from_string(value):
    """
    Convert string "[5, 6]" to a real python array.
    """
    if isinstance(value, list):
        return value
    value = ast.literal_eval(value)
    if isinstance(value, list):
        return value
    return []


class Settings(KeyValueConfigFile):
    DAILY = 24
    HOURLY = 1
    WEEKLY = 168
    MONTHLY = 720

    _fields = [
        ('username', str, None),
        ('accesstoken', str, None),
        ('repositoryname', str, None),
        ('remotehost', str, None),
        ('remoteurl', str, None),
        ('remoterole', int, None),
        ('schedule', int, DAILY),
        ('configured', _bool, False),
        ('pause_until', lambda x: Datetime(x) if x else None, None),
        ('diskid', str, None),
        ('maxage', int, None),
        ('ignore_weekday', list_from_string, None),
        ('keepdays', int, None),
        ('maxage', int, None),
        # Load default value from environment variable to ease unittest
        (
            'check_latest_version',
            lambda x: os.environ.get('MINARCA_CHECK_LATEST_VERSION', str(x)).lower() in ['true', 'True', '1'],
            True,
        ),
        ('localmountpoint', str, None),
        ('localuuid', str, None),
        ('localrelpath', str, None),
        ('localcaption', str, None),
        ('pre_hook_command', str, None),
        ('post_hook_command', str, None),
        ('ignore_hook_errors', _bool, False),
    ]

    @property
    def remote(self):
        return self.diskid is None
