# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import os
import unittest
from pathlib import Path

from minarca_client.core.compat import IS_LINUX, IS_WINDOWS
from minarca_client.core.disk import get_location_info, list_disk_with_location_info, list_disks, splitmountpoint


class TestDisk(unittest.TestCase):
    @unittest.skipIf(IS_LINUX, 'linux testing is run in container without abilities to create block device')
    def test_get_location_info(self):
        filename = os.getcwd()
        disk_info = get_location_info(Path(filename))
        self.assertTrue(disk_info.mountpoint)
        self.assertTrue(disk_info.relpath)
        self.assertTrue(disk_info.fstype)
        self.assertIsNotNone(disk_info.caption)
        self.assertIsNotNone(disk_info.removable)
        self.assertIsNotNone(disk_info.device_type)

    @unittest.skipUnless(IS_WINDOWS, 'case-insensitive only work on Windows OS')
    def test_get_location_info_case_insensitive(self):
        # Given a drive file name in lowercase
        filename = os.getcwd()
        # Then it should match without case sensitivity
        self.assertIsNotNone(get_location_info(Path(filename.upper())))
        self.assertIsNotNone(get_location_info(Path(filename.lower())))

    def test_list_disks(self):
        # Not sure how to test this in a controlled environment.
        # Result is different in every environment.
        disks = list_disks()
        self.assertTrue(disks)
        disk = disks[0]
        self.assertIsInstance(disk, Path)

    def test_list_disk_with_location_info_removable(self):
        # Not sure how to test this in a controlled environment.
        # We don't have removable disk in CICD.
        # Result is different in every environment.
        disks = list_disk_with_location_info()
        for disk in disks:
            self.assertIsInstance(disk.mountpoint, Path)
            self.assertEqual(Path("."), disk.relpath)
            self.assertTrue(disk.is_mountpoint)
        disks = list_disk_with_location_info(removable=1)
        for disk in disks:
            self.assertIsInstance(disk.mountpoint, Path)
            self.assertEqual(Path("."), disk.relpath)
            self.assertTrue(disk.is_mountpoint)

    def test_splitmountpoint(self):
        if IS_WINDOWS:
            mountpoint, relpath = splitmountpoint("//servername/host")
            self.assertEqual(Path('//servername/host/'), mountpoint)
            self.assertEqual(Path('.'), relpath)
            mountpoint, relpath = splitmountpoint("//servername/host/minarca/test")
            self.assertEqual(Path('//servername/host'), mountpoint)
            self.assertEqual(Path('minarca/test'), relpath)
            mountpoint, relpath = splitmountpoint("q:/")
            self.assertEqual(Path('q:/'), mountpoint)
            self.assertEqual(Path('.'), relpath)
