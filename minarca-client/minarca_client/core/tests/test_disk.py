import os
import unittest

from minarca_client.core.compat import IS_LINUX, IS_WINDOWS
from minarca_client.core.disk import get_location_info, list_disks


class TestDisk(unittest.TestCase):
    @unittest.skipIf(IS_LINUX, 'linux testing is run in container without abilities to create block device')
    def test_get_location_info(self):
        filename = os.getcwd()
        disk_info = get_location_info(filename)
        self.assertTrue(disk_info.device)
        self.assertTrue(disk_info.mountpoint)
        self.assertTrue(disk_info.relpath)
        self.assertTrue(disk_info.fstype)
        self.assertIsNotNone(disk_info.caption)
        self.assertIsNotNone(disk_info.removable)
        self.assertGreater(disk_info.free, 0)
        self.assertGreater(disk_info.used, 0)
        self.assertGreater(disk_info.size, 0)

    @unittest.skipUnless(IS_WINDOWS, 'case-insensitive only work on Windows OS')
    def test_get_location_info_case_insensitive(self):
        # Given a drive file name in lowercase
        filename = os.getcwd()
        # Then it should match without case sensitivity
        self.assertIsNotNone(get_location_info(filename.upper()))
        self.assertIsNotNone(get_location_info(filename.lower()))

    def test_list_disks(self):
        # Not sure how to test this in a controlled environment.
        # Result is different in every environment.
        disks = list_disks()
        if not IS_LINUX:
            self.assertTrue(disks)
