'''
Created on Jul. 5, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import unittest
from minarca_client.ui.theme import MINARCA_ICON
import os


class TestTheme(unittest.TestCase):

    def test_minarca_icon(self):
        self.assertIsNotNone(MINARCA_ICON)
        self.assertTrue(os.path.isfile(MINARCA_ICON))
