'''
Created on Dec. 8, 2020

@author: Patrik Dufresne
'''
import unittest
from unittest.mock import patch

from minarca_quota_api.zfs_quota import set_quota, get_quota


@patch('minarca_quota_api.zfs_quota.subprocess.check_output')
class ZFSQuotaTest(unittest.TestCase):

    def test_set_quota(self, check_output_mock):
        set_quota('tank', quota=54321, projectid=1)

    def test_get_quota(self, check_output_mock):
        # Test with no quota
        check_output_mock.return_value = '-\n-\n'
        self.assertEqual({'size': 0, 'used': 0}, get_quota('tank', projectid=1))

        # Test with values
        check_output_mock.return_value = '1234\n5678\n'
        self.assertEqual({'size': 5678, 'used': 1234}, get_quota('tank', projectid=1))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
