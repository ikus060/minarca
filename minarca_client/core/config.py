# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 8, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import datetime
import time
from functools import total_ordering
from pathlib import Path
from typing import Any

import javaproperties


@total_ordering
class Datetime:
    """
    Friendly class to manipulate date in configuration file.
    """

    def __init__(self, epoch_ms=None):
        if epoch_ms is None:
            epoch_ms = int(time.time() * 1000)
        self.epoch_ms = int(epoch_ms)

    def __str__(self):
        return str(int(self))

    def __repr__(self):
        return 'Datetime(%s)' % self.epoch_ms

    def __int__(self):
        return self.epoch_ms

    def __eq__(self, other):
        return hasattr(other, 'epoch_ms') and self.epoch_ms == other.epoch_ms

    def __lt__(self, other):
        return self.epoch_ms < other.epoch_ms

    def __sub__(self, other):
        if isinstance(other, Datetime):
            return datetime.timedelta(milliseconds=self.epoch_ms - other.epoch_ms)
        elif isinstance(other, datetime.timedelta):
            return Datetime(epoch_ms=self.epoch_ms - (other.total_seconds() * 1000))
        raise TypeError("unsupported operand type(s) for -: 'Datetime' and '%s'" % other.__class__.__name__)

    def __add__(self, other):
        if isinstance(other, Datetime):
            return datetime.timedelta(milliseconds=self.epoch_ms + other.epoch_ms)
        elif isinstance(other, datetime.timedelta):
            return Datetime(epoch_ms=self.epoch_ms + (other.total_seconds() * 1000))
        raise ValueError()

    def strftime(self, fmt='%Y-%m-%dT%H:%M:%S%z'):
        return time.strftime(fmt, time.localtime(self.epoch_ms / 1000))


class KeyValueConfigFile:
    """
    Configurated with key value supporting getter and setter.
    """

    def __init__(self, raw_data={}):
        data = {field: default for field, unused, default in self._fields}
        # Then read values field by field, use default if not defined otherwise try to coerse the value.
        for field, coerse, default in self._fields:
            value = raw_data.get(field, None)
            if value is None:
                data[field] = default
            else:
                try:
                    data[field] = coerse(value)
                except (ValueError, KeyError):
                    data[field] = default
        self._data = data

    @classmethod
    def from_file(cls, path: Path):
        raw_data = {}
        try:
            with open(path, 'r', encoding='latin-1') as f:
                # Read raw data from java properties files.
                raw_data = javaproperties.load(f)
        except FileNotFoundError:
            pass
        return cls(raw_data)

    def save_file(self, path):
        values = {
            field: str(self._data.get(field)) for field, *unused in self._fields if self._data.get(field) is not None
        }
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + '.tmp')
        with tmp.open('w', encoding='latin-1') as f:
            javaproperties.dump(values, f)
        tmp.replace(path)

    def __getattr__(self, name: str) -> Any:
        # Check if name is valid
        if name not in [f for f, *unused in self._fields]:
            raise AttributeError(name)
        # If not, we need to reload the file.
        return self._data.get(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            # Attribute starting with "_" are private variables.
            super().__setattr__(name, value)
        else:
            # Check if name is valid
            for f, coerse, unused in self._fields:
                if name == f:
                    # Update dict
                    self._data[name] = coerse(value)
                    return
            raise AttributeError(name)

    def clear(self):
        """
        Restore defaults.
        """
        self._data = {field: default for field, unused, default in self._fields}
