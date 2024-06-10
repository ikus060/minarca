# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 8, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import ast
import datetime
import logging
import os
import re
import time
from collections import namedtuple
from collections.abc import MutableSequence
from functools import total_ordering
from typing import Any

import javaproperties
import psutil

from minarca_client.core.compat import IS_LINUX, IS_MAC, IS_WINDOWS, get_config_home, get_home, get_temp
from minarca_client.locale import _

logger = logging.getLogger(__name__)


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

    def strftime(self, fmt):
        return time.strftime(fmt, time.localtime(self.epoch_ms / 1000))


class AbstractConfigFile:
    def __init__(self, filename: str):
        assert filename, 'a filename is required'
        self._fn = filename
        self._data = None
        self.reload()

    def reload(self):
        """
        Check if the file changed since last loading. If not does nothing. Othersiw will read the file data.
        """
        self._data = self._load()

    def _load(self):
        raise NotImplementedError()

    def save(self):
        raise NotImplementedError()

    def __enter__(self):
        # Load file content.
        self.reload()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Save changes in all cases.
        self.save()


class KeyValueConfigFile(AbstractConfigFile):
    """
    Configurated with key value supporting getter and setter.
    """

    def __init__(self, filename: str):
        assert self._fields, 'subclass must define list of fields'
        super().__init__(filename)

    def _load(self):
        data = {field: default for field, unused, default in self._fields}
        try:
            with open(self._fn, 'r', encoding='latin-1') as f:
                # Read raw data from java properties files.
                raw_data = javaproperties.load(f)
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
        except FileNotFoundError:
            pass
        return data

    def save(self):
        values = {
            field: str(self._data.get(field)) for field, *unused in self._fields if self._data.get(field) is not None
        }
        with open(self._fn, 'w', encoding='latin-1') as f:
            javaproperties.dump(values, f)

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


LAST_RESULTS = ['SUCCESS', 'FAILURE', 'RUNNING', 'STALE', 'INTERRUPT']


def _default(cls, default_value=None):
    def func(x):
        if x is None:
            return default_value
        else:
            return cls(x)

    return func


class Status(KeyValueConfigFile):
    RUNNING_DELAY = 5  # When running status file get updated every 5 seconds.

    _fields = [
        ('details', str, None),
        ('lastdate', lambda x: Datetime(x) if x else None, None),
        ('lastresult', lambda x: x if x in LAST_RESULTS else 'UNKNOWN', 'UNKNOWN'),
        ('lastsuccess', lambda x: Datetime(x) if x else None, None),
        ('pid', int, None),
        ('action', lambda x: x if x in ['backup', 'restore'] else None, None),
        ('lastnotificationid', str, None),
        ('lastnotificationdate', lambda x: Datetime(x) if x else None, None),
    ]

    @property
    def current_status(self):
        """
        Return a backup status. Read data from the status file and make
        interpretation of it.
        """
        now = Datetime()
        # After reading the status file, let determine the real status.
        data = dict(self._data)
        if data.get('lastresult') == 'RUNNING':
            # Get pid and checkif process is running.
            pid = data.get('pid')
            if not pid:
                return 'INTERRUPT'
            try:
                psutil.Process(data.get('pid')).is_running()
            except (ValueError, psutil.NoSuchProcess):
                return 'INTERRUPT'
            # Then let check if the status file was updated within the last 10 seconds.
            lastdate = data.get('lastdate')
            if lastdate and now - lastdate > datetime.timedelta(seconds=self.RUNNING_DELAY * 2):
                return 'STALE'
        # By default return lastresult value.
        return data.get('lastresult')


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
        ('schedule', int, DAILY),
        ('configured', lambda x: x in [True, 'true', 'True', '1'], False),
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
        ('localuuid', str, None),
        ('localrelpath', str, None),
        ('localcaption', str, None),
    ]

    @property
    def remote(self):
        return self.diskid is None


class InvalidPatternError(Exception):
    """
    Raised when a pattern file contains an invalid line.
    """

    pass


Pattern = namedtuple('Pattern', ['include', 'pattern', 'comment'])
Pattern.is_wildcard = lambda self: '*' in self.pattern or '?' in self.pattern or '[' in self.pattern


class Patterns(AbstractConfigFile, MutableSequence):
    def _load(self):
        data = []
        try:
            with open(self._fn, 'r', encoding='utf-8', errors='replace') as f:
                comment = None
                for line in f.readlines():
                    line = line.rstrip()
                    # Skip comment
                    if line.startswith("#") or not line.strip():
                        comment = line[1:].strip()
                        continue
                    if line[0] not in ['+', '-']:
                        raise InvalidPatternError(line)
                    include = line[0] == '+'
                    try:
                        data.append(Pattern(include, line[1:], comment))
                    except ValueError:
                        # Ignore duplicate pattern
                        pass
                    comment = None
        except FileNotFoundError:
            data = []
        return data

    def __getitem__(self, idx):
        return self._data[idx]

    def __setitem__(self, idx, value):
        assert isinstance(value, Pattern), 'this collection only support pattern'
        # Update list
        self._data[idx] = value

    def __delitem__(self, idx):
        del self._data[idx]

    def __len__(self):
        return len(self._data)

    def insert(self, index, value):
        assert isinstance(value, Pattern), 'this collection only support pattern'
        # Make sure to remove opposite pattern
        for item in self._data:
            if item.pattern == value.pattern:
                self.remove(item)
        self._data.insert(index, value)

    @classmethod
    def defaults(cls):
        """
        Restore defaults patterns.
        """
        data = []
        # Add user's documents
        data.append(Pattern(True, os.path.join(get_home(), 'Documents'), _("User's Documents")))
        # Add Minarca config
        data.append(Pattern(True, os.path.join(get_config_home(), 'patterns*'), _("Minarca Config")))

        if IS_WINDOWS:
            data.extend(
                [
                    Pattern(False, "**/Thumbs.db", _("Thumbnails cache")),
                    Pattern(False, "**/desktop.ini", _("Arrangement of a Windows folder")),
                    Pattern(False, "C:/swapfile.sys", _("Swap System File")),
                    Pattern(False, "C:/pagefile.sys", _("Page System File")),
                    Pattern(False, "C:/hiberfil.sys", _("Hibernation System File")),
                    Pattern(False, "C:/System Volume Information", _("System Volume Information")),
                    Pattern(False, "C:/Recovery/", _("System Recovery")),
                    Pattern(False, "C:/$Recycle.Bin/", _("Recycle bin")),
                    Pattern(False, get_temp(), _("Temporary Folder")),
                    Pattern(False, "**/*.bak", _("AutoCAD backup files")),
                    Pattern(False, "**/~$*", _("Office temporary files")),
                    Pattern(False, "**/*.ost.tmp", _("Outlook IMAP temporary files")),
                    Pattern(False, "**/*.pst.tmp", _("Outlook POP temporary files")),
                ]
            )
        elif IS_MAC:
            data.extend(
                [
                    Pattern(False, "**/.DS_Store", _("Desktop Services Store")),
                ]
            )
        elif IS_LINUX:
            data.extend(
                [
                    Pattern(False, "/dev", _("dev filesystem")),
                    Pattern(False, "/proc", _("proc filesystem")),
                    Pattern(False, "/sys", _("sys filesystem")),
                    Pattern(False, "/tmp", _("Temporary Folder")),
                    Pattern(False, "/run", _("Volatile program files")),
                    Pattern(False, "/mnt", _("Mounted filesystems")),
                    Pattern(False, "/media", _("External media")),
                    Pattern(False, "**/lost+found", _("Ext4 Lost and Found")),
                    Pattern(False, "**/.~*", _("Hidden temporary files")),
                    Pattern(False, "**/*~", _("Vim Temporary files")),
                ]
            )
        return data

    def save(self):
        """
        Write all the pattern to the file.
        """
        with open(self._fn, 'w', encoding='utf-8') as f:
            for pattern in self._data:
                # Write comments if any
                if pattern.comment:
                    f.write("# %s\n" % pattern.comment.strip())
                # Write patterns
                f.write(('+%s\n' if pattern.include else '-%s\n') % pattern.pattern)

    def group_by_roots(self):
        """
        Return the list of patterns for each root. On linux, we have a single root. On Windows,
        we might have multiple if the computer has multiple disk, like C:, D:, etc.
        """
        # Determine each prefix.
        if IS_WINDOWS:
            # On Windows, Find list of drives from patterns
            prefixes = list()
            for p in self:
                m = re.match(r'^[A-Z]:[\\/]', p.pattern)
                if p.include and m:
                    drive = m.group(0).replace('\\', '/')
                    if drive not in prefixes:
                        prefixes.append(drive)
        else:
            # On Unix, simply use '/'
            prefixes = ['/']

        # Organize patterns
        if len(self):
            for prefix in prefixes:
                sublist = []
                for p in self:
                    pattern = p.pattern.replace('\\', '/') if IS_WINDOWS else p.pattern
                    if pattern.startswith(prefix):
                        sublist.append(Pattern(p.include, pattern, None))
                    elif pattern.startswith('**') and not p.include:
                        sublist.append(Pattern(p.include, pattern, None))
                    elif p.is_wildcard() and not p.include:
                        sublist.append(Pattern(p.include, '**/' + pattern, None))
                # Then sort include / exclude from most precise to least precise
                # absolute path first, then longuer path, then exclude value.
                sublist = sorted(
                    sublist,
                    key=lambda p: (
                        not p.pattern.startswith('**'),  # exclude wildcard pattern, should be first.
                        -len(p.pattern.split('/')),  # Longuer path define before shorter path.
                        p.include,  # Exclude define before includes
                        p.pattern,
                    ),
                )
                yield (prefix, sublist)
