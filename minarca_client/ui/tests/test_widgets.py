'''
Created on Jul 12, 2021

@author: vmtest
'''
import unittest
from minarca_client.ui.widgets import Dialog, show_info
from unittest import mock
from unittest.case import skipUnless
from minarca_client.core.compat import HAS_DISPLAY


@skipUnless(HAS_DISPLAY, 'run test with UI only if display is available')
class MessageBoxTest(unittest.TestCase):

    def setUp(self):
        self.dlg = Dialog()
        self.dlg.create()
        self.dlg.pump_events()

    def tearDown(self):
        self.dlg.close()
        self.dlg.pump_events()

    @mock.patch('tkinter.commondialog.Dialog._fixoptions', side_effect=ZeroDivisionError)
    def test_show_info(self, *mock):
        with self.assertRaises(ZeroDivisionError):
            show_info(self.dlg.window, 'title', 'message', 'detail')
        self.dlg.pump_events()


if __name__ == "__main__":
    unittest.main()
