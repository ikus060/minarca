# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Oct 18, 2024

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import glob
import os
import re
from collections import namedtuple
from collections.abc import MutableSequence

from minarca_client.core.compat import IS_LINUX, IS_MAC, IS_WINDOWS, get_config_home, get_home, get_temp
from minarca_client.core.config import AbstractConfigFile
from minarca_client.locale import _

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
                    # Silently ignore invalid patterns
                    if line[0] not in ['+', '-']:
                        continue
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

        def _append(p):
            if p.is_wildcard():
                for m in glob.iglob(p.pattern, recursive=True):
                    data.append(p)
                    return
            elif os.path.exists(p.pattern):
                data.append(p)

        # Add user's documents
        _append(Pattern(True, str(get_home() / 'Documents'), _("User's Documents")))
        # Add Minarca config
        _append(Pattern(True, str(get_config_home() / 'patterns*'), _("Minarca Config")))

        if IS_WINDOWS:
            _append(
                Pattern(
                    True,
                    str(get_home() / 'AppData/Roaming/Mozilla/Firefox/Profiles/*/places.sqlite'),
                    _("Firefox Bookmark"),
                )
            )
            _append(
                Pattern(
                    True,
                    str(get_home() / 'AppData/Local/Google/Chrome/User Data/Default/Bookmarks'),
                    _("Chrome Bookmark"),
                )
            )
            _append(
                Pattern(
                    True,
                    str(get_home() / 'AppData/Local/Microsoft/Outlook/*.?st'),
                    _("Outlook Offline Data"),
                )
            )
            _append(
                Pattern(
                    True,
                    str(get_home() / 'AppData/Local/Microsoft/Outlook/Offline Address Books'),
                    _("Outlook Address Books"),
                )
            )
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
                    Pattern(False, str(get_temp()), _("Temporary Folder")),
                    Pattern(False, "**/*.bak", _("AutoCAD backup files")),
                    Pattern(False, "**/~$*", _("Office temporary files")),
                    Pattern(False, "**/*.ost.tmp", _("Outlook IMAP temporary files")),
                    Pattern(False, "**/*.pst.tmp", _("Outlook POP temporary files")),
                    Pattern(False, "**/*.ddb.bak", _("Dynacom Backup file")),
                    Pattern(False, "**/.tmp.driveupload", _("Google Drive temporary upload files")),
                    Pattern(False, "**/.tmp.drivedownload", _("Google Drive temporary download files")),
                    # Ignore OneDrive special GUID file
                    Pattern(
                        False,
                        "**/OneDrive*/.*[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]",
                        _("OneDrive GUID File"),
                    ),
                    # Ignore Google Drive special folders
                    Pattern(False, "**/.shortcut-targets-by-id", _("Google Drive Shortcut Metadata")),
                    Pattern(False, "**/.file-revisions-by-id", _("Google Drive Revision History")),
                    Pattern(False, "**/.Encrypted", _("Google Drive Encrypted")),
                ]
            )
        elif IS_MAC:
            _append(
                Pattern(
                    True,
                    str(get_home() / 'Library/Application Support/Firefox/Profiles/*/places.sqlite'),
                    _("Firefox Bookmark"),
                )
            )
            _append(
                Pattern(
                    True,
                    str(get_home() / 'Library/Application Support/Google/Chrome/Default/Bookmarks'),
                    _("Chrome Bookmark"),
                )
            )
            data.extend(
                [
                    Pattern(False, "**/.DS_Store", _("Desktop Services Store")),
                    Pattern(
                        False,
                        "**/OneDrive*/.*[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]-[0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f]",
                        _("OneDrive GUID File"),
                    ),
                ]
            )
        elif IS_LINUX:
            _append(Pattern(True, str(get_home() / '.mozilla/firefox/*/places.sqlite'), _("Firefox Bookmark")))
            _append(Pattern(True, str(get_home() / '.config/google-chrome/Default/Bookmarks'), _("Chrome Bookmark")))
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
                    Pattern(False, "**/*~", _("Vim temporary files")),
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
