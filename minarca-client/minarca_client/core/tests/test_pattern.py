# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 7, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import os
import tempfile
import unittest
from unittest.case import skipIf

from minarca_client.core.compat import IS_WINDOWS
from minarca_client.core.pattern import Pattern, Patterns

_home = 'C:/Users' if IS_WINDOWS else '/home'


class PatternTest(unittest.TestCase):
    def test_is_wildcard(self):
        self.assertTrue(Pattern(True, '*.bak', None).is_wildcard())
        self.assertTrue(Pattern(True, '**/temp', None).is_wildcard())
        self.assertFalse(Pattern(True, '.', None).is_wildcard())
        self.assertFalse(Pattern(True, '..', None).is_wildcard())
        self.assertFalse(Pattern(True, _home, None).is_wildcard())


class PatternsTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def test_defaults(self):
        patterns = Patterns('patterns')
        self.assertEqual(0, len(patterns))
        data = patterns.defaults()
        self.assertNotEqual(0, len(data))

    def test_load(self):
        with open('patterns', 'w') as f:
            f.write("# comments\n")
            f.write("+somefilename.txt\n")
            f.write("# AutoCad Backup file\n")
            f.write("-*.bak\n")
        # When reading the pattern file
        patterns = Patterns('patterns')
        # Then we have 2 patterns
        self.assertEqual(Pattern(True, 'somefilename.txt', 'comments'), patterns[0])
        self.assertEqual(Pattern(False, '*.bak', 'AutoCad Backup file'), patterns[1])

    def test_load_with_empty_lines(self):
        with open('patterns', 'w') as f:
            f.write("# comments\n")
            f.write("+somefilename.txt\n")
            f.write("\n")
            f.write("# AutoCad Backup file\n")
            f.write("-*.bak\n")
        patterns = Patterns('patterns')
        self.assertEqual(Pattern(True, 'somefilename.txt', 'comments'), patterns[0])
        self.assertEqual(Pattern(False, '*.bak', 'AutoCad Backup file'), patterns[1])

    def test_load_with_missing_file(self):
        patterns = Patterns('invalid')
        self.assertEqual(0, len(patterns))

    def test_load_wrong_encoding(self):
        # Given a file with invalid encoding
        with open('patterns', 'w', encoding='latin1') as f:
            f.write("# comments\n")
            f.write("+éric_file.txt\n")
            f.write("# Ignore Backup file\n")
            f.write("-*.bak\n")
        # When reading the pattern file
        patterns = Patterns('patterns')
        # Then we have 2 patterns sorted
        self.assertEqual(Pattern(include=True, pattern='�ric_file.txt', comment='comments'), patterns[0])
        self.assertEqual(Pattern(False, '*.bak', 'Ignore Backup file'), patterns[1])

    def test_load_with_invalid_line(self):
        # Given a file with invalid line
        with open('patterns', 'w', encoding='latin1') as f:
            f.write("# comments\n")
            f.write("+/this-is-a-set\n")
            f.write("invalid-line\n")
            f.write("-*.bak\n")
        # When reading the pattern file
        patterns = Patterns('patterns')
        # Then we have 2 patterns sorted
        self.assertEqual(Pattern(include=True, pattern='/this-is-a-set', comment='comments'), patterns[0])
        self.assertEqual(Pattern(False, '*.bak', comment=None), patterns[1])

    def test_save(self):
        with open('patterns', 'w') as f:
            f.write("")
        patterns = Patterns('patterns')
        patterns.append(Pattern(True, '*.bak', 'AutoCAD Backup file'))
        patterns.append(Pattern(True, '$~*', 'Office Temporary files'))
        patterns.save()
        with open('patterns', 'r') as f:
            data = f.read()
        self.assertEqual("# AutoCAD Backup file\n+*.bak\n# Office Temporary files\n+$~*\n", data)

    def test_transaction(self):
        # Given a pattern file
        with open('patterns', 'w') as f:
            f.write("")
        patterns = Patterns('patterns')
        # When starting a transaction
        with patterns as t:
            t.append(Pattern(True, '*.bak', 'AutoCAD Backup file'))
            t.append(Pattern(True, '$~*', 'Office Temporary files'))

            # Then changes are not saved to file.
            with open('patterns', 'r') as f:
                data = f.read()
            self.assertEqual("", data)
        # Then after transaction, changes are saved.
        with open('patterns', 'r') as f:
            data = f.read()
        self.assertEqual("# AutoCAD Backup file\n+*.bak\n# Office Temporary files\n+$~*\n", data)

    @skipIf(IS_WINDOWS, 'only or unix')
    def test_group_by_roots_unix_wildcard(self, *unused):
        with open('patterns', 'w') as f:
            f.write("")
        patterns = Patterns('patterns')
        patterns.append(Pattern(True, '/home/', None))
        patterns.append(Pattern(False, '**/*.bak', None))
        patterns.append(Pattern(False, '*.tmp', None))
        patterns.append(Pattern(False, '/home/*.tmp', None))
        patterns.append(Pattern(True, '/srv/', None))
        patterns.append(Pattern(False, '/srv/jellyfin/config/transcodes', None))
        # should be ignored, because everything is included by default.
        patterns.append(Pattern(True, '**/*.include', None))
        self.assertEqual(
            [
                (
                    '/',
                    [
                        Pattern(False, '**/*.bak', None),
                        Pattern(False, '**/*.tmp', None),
                        Pattern(False, '/srv/jellyfin/config/transcodes', None),
                        Pattern(False, '/home/*.tmp', None),
                        Pattern(True, '/home/', None),
                        Pattern(True, '/srv/', None),
                    ],
                )
            ],
            list(patterns.group_by_roots()),
        )

    @skipIf(not IS_WINDOWS, 'only for windows')
    def test_group_by_roots_win(self, *unused):
        with open('p', 'w') as f:
            f.write("")
        p = Patterns('p')
        p.append(Pattern(True, 'C:/foo', None))
        p.append(Pattern(False, '**/*.bak', None))
        p.append(Pattern(True, 'C:\\bar', None))
        p.append(Pattern(False, '**/$~*', None))
        p.append(Pattern(True, 'D:\\bar', None))
        p.append(Pattern(False, '*.tmp', None))
        groups = list(p.group_by_roots())
        self.assertEqual(
            [
                (
                    'C:/',
                    [
                        Pattern(False, '**/$~*', None),
                        Pattern(False, '**/*.bak', None),
                        Pattern(False, '**/*.tmp', None),
                        Pattern(True, 'C:/bar', None),
                        Pattern(True, 'C:/foo', None),
                    ],
                ),
                (
                    'D:/',
                    [
                        Pattern(False, '**/$~*', None),
                        Pattern(False, '**/*.bak', None),
                        Pattern(False, '**/*.tmp', None),
                        Pattern(True, 'D:/bar', None),
                    ],
                ),
            ],
            groups,
        )

    @skipIf(not IS_WINDOWS, 'only for windows')
    def test_group_by_roots_win_exclude_other_root(self, *unused):
        p = Patterns('p')
        p.append(Pattern(True, 'C:/foo', None))
        p.append(Pattern(False, '**/*.bak', None))
        # should be ignored, because everything is included by default.
        p.append(Pattern(True, '**/*.include', None))
        p.append(Pattern(True, 'C:\\bar', None))
        p.append(Pattern(False, '**/$~*', None))
        p.append(Pattern(False, 'D:\\bar', None))
        groups = list(p.group_by_roots())
        self.assertEqual(
            [
                (
                    'C:/',
                    [
                        Pattern(False, '**/$~*', None),
                        Pattern(False, '**/*.bak', None),
                        Pattern(True, 'C:/bar', None),
                        Pattern(True, 'C:/foo', None),
                    ],
                ),
            ],
            groups,
        )
