# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 8, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import datetime
import os
import re
import time
from collections import namedtuple
from functools import total_ordering

import javaproperties

from minarca_client.core.compat import IS_LINUX, IS_MAC, IS_WINDOWS, get_home, get_temp
from minarca_client.locale import _


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
        return time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(self.epoch_ms / 1000))

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
            return Datetime(epoch_ms=self.epoch_ms - other.total_seconds())
        raise ValueError()

    def __add__(self, other):
        if isinstance(other, Datetime):
            return datetime.timedelta(milliseconds=self.epoch_ms + other.epoch_ms)
        elif isinstance(other, datetime.timedelta):
            return Datetime(epoch_ms=self.epoch_ms + other.total_seconds())
        raise ValueError()


class Status(dict):
    """
    Used to persists backup status.
    """

    LAST_RESULTS = ['SUCCESS', 'FAILURE', 'UNKNOWN', 'RUNNING', 'STALE', 'INTERRUPT']
    _DEFAULT = {'details': None, 'lastdate': None, 'lastresult': 'UNKNOWN', 'lastsuccess': None, 'pid': None}

    def __init__(self, filename):
        assert filename
        self.filename = filename
        self._load()

    def save(self):
        values = {
            k: str(int(v)) if k in ['lastdate', 'lastsuccess'] else str(v) for k, v in self.items() if v is not None
        }
        with open(self.filename, 'w', encoding='latin-1') as f:
            return javaproperties.dump(values, f)

    def _load(self):
        self.clear()
        self.update(self._DEFAULT)
        if not os.path.exists(self.filename):
            return
        with open(self.filename, 'r', encoding='latin-1') as f:
            self.update(javaproperties.load(f))
            # Convert date from epoch in milliseconds
            for field in ['lastdate', 'lastsuccess']:
                if self[field]:
                    try:
                        self[field] = Datetime(self[field])
                    except (ValueError, KeyError):
                        self[field] = None


class Settings(dict):
    """
    Used to store minarca settings in `minarca.properties`
    """

    DAILY = 24
    HOURLY = 1
    WEEKLY = 168
    MONTHLY = 720

    _DEFAULT = {
        'username': None,
        'repositoryname': None,
        'remotehost': None,
        'remoteurl': None,
        'schedule': DAILY,
        'configured': False,
        'pause_until': None,
        # Load default value from environment variable to ease unittest
        'check_latest_version': os.environ.get('MINARCA_CHECK_LATEST_VERSION', 'True') in [True, 'true', 'True', '1'],
    }

    def __init__(self, filename):
        assert filename
        self.filename = filename
        self._load()

    def save(self):
        values = {k: str(int(v)) if k in ['pause_until'] else str(v) for k, v in self.items() if v is not None}
        with open(self.filename, 'w', encoding='latin-1') as f:
            return javaproperties.dump(values, f)

    def _load(self):
        self.clear()
        self.update(self._DEFAULT)
        if not os.path.exists(self.filename):
            return
        with open(self.filename, 'r', encoding='latin-1') as f:
            self.update(javaproperties.load(f))
            # schedule is an integer
            try:
                self['schedule'] = int(self['schedule'])
            except (ValueError, KeyError):
                self['schedule'] = self._DEFAULT.get('schedule')
            # boolean fields
            for key in ['configured', 'check_latest_version']:
                try:
                    self[key] = self[key] in [True, 'true', 'True', '1']
                except KeyError:
                    self[key] = self._DEFAULT.get(key)
            # pause_until is a date
            try:
                self['pause_until'] = Datetime(self['pause_until']) if self['pause_until'] else None
            except (ValueError, KeyError):
                self['pause_until'] = None


class InvalidPatternError(Exception):
    """
    Raised when a pattern file contains an invalid line.
    """

    pass


Pattern = namedtuple('Pattern', ['include', 'pattern', 'comment'])
Pattern.is_wildcard = lambda self: '*' in self.pattern or '?' in self.pattern or '[' in self.pattern


class Patterns(list):
    def __init__(self, filename):
        assert filename
        self.filename = filename
        self._load()

    def _load(self):
        self.clear()
        if not os.path.exists(self.filename):
            return
        with open(self.filename, 'r', encoding='utf-8', errors='replace') as f:
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
                    self.append(Pattern(include, line[1:], comment))
                except ValueError:
                    # Ignore duplicate pattern
                    pass
                comment = None

    def append(self, p):
        """
        Check for duplicate pattern.
        """
        # Make sure to remove opposite pattern
        for item in self:
            if item.pattern == p.pattern:
                self.remove(item)
        super().append(p)

    def extend(self, other_patterns):
        """
        Check for duplicate pattern.
        """
        for p in other_patterns:
            self.append(p)

    def defaults(self):
        """
        Restore defaults patterns.
        """
        self.clear()
        self.extend(
            [
                Pattern(True, os.path.join(get_home(), 'Documents'), _("User's Documents")),
            ]
        )

        if IS_WINDOWS:
            self.extend(
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
        if IS_MAC:
            self.extend(
                [
                    Pattern(False, "**/.DS_Store", _("Desktop Services Store")),
                ]
            )
        if IS_LINUX:
            self.extend(
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

    def save(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            self.write(f)

    def write(self, f):
        assert f
        assert hasattr(f, 'write')
        for pattern in self:
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
                m = re.match('^[A-Z]:(\\\\|/)', p.pattern)
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
                # absolute path first, then longuer path, then exclude value
                sublist = sorted(
                    sublist,
                    key=lambda p: (p.pattern.startswith('**'), -len(p.pattern.split('/')), p.include, p.pattern),
                )
                yield (prefix, sublist)
