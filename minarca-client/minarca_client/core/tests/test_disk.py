import os
import unittest

from minarca_client.core.compat import IS_LINUX
from minarca_client.core.disk import get_disk_info, list_disks


class TestDisk(unittest.TestCase):

    @unittest.skipIf(IS_LINUX, 'linux testing is run in container without abilities to create block device')
    def test_get_disk_info(self):
        filename = os.getcwd()
        disk_info = get_disk_info(filename)
        self.assertTrue(disk_info.device)
        self.assertTrue(disk_info.mountpoint)
        self.assertTrue(disk_info.relpath)
        self.assertTrue(disk_info.fstype)
        self.assertIsNotNone(disk_info.caption)
        self.assertIsNotNone(disk_info.removable)
        self.assertGreater(disk_info.free, 0)
        self.assertGreater(disk_info.used, 0)
        self.assertGreater(disk_info.size, 0)

    def test_list_disks(self):
        # Not sure how to test this in a controlled environment.
        # Result is different in every environment.
        disks = list_disks()
        if not IS_LINUX:
            self.assertTrue(disks)
