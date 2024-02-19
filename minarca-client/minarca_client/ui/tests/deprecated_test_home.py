'''
Created on Jul. 20, 2021

@author: ikus060
'''
import os
import tempfile
import tkinter
import unittest
from contextlib import contextmanager
from unittest import mock

from minarca_client.core.compat import IS_LINUX, IS_WINDOWS
from minarca_client.ui.backup_main import MainDialog

NO_DISPLAY = not os.environ.get('DISPLAY', False)


@contextmanager
def new_dialog(cls):
    def pump_events():
        while dlg.root.dooneevent(tkinter._tkinter.ALL_EVENTS | tkinter._tkinter.DONT_WAIT):
            pass

    dlg = cls()
    dlg.pump_events = pump_events
    try:
        yield dlg
    finally:
        dlg.pump_events()
        dlg.destroy()
        dlg.pump_events()


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
class HomeTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        os.environ['MINARCA_CONFIG_HOME'] = self.tmp.name
        os.environ['MINARCA_DATA_HOME'] = self.tmp.name
        os.environ['MINARCA_CHECK_LATEST_VERSION'] = 'False'

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    @mock.patch('minarca_client.ui.home.webbrowser')
    def test_invoke_show_help(self, mock_webbrowser):
        with new_dialog(MainDialog) as dlg:
            # Given a remotehost
            dlg.backup.settings.remoteurl = 'http://examples.com'
            # Given a Home dialog with help button
            dlg.pump_events()
            self.assertIsNotNone(dlg.status_view.start_button)
            # When invoking the button
            dlg.help_button.invoke()
            dlg.pump_events()
            # Then backup start
            mock_webbrowser.open.assert_called_once_with('http://examples.com/help')

    @unittest.skipIf(IS_WINDOWS, 'this test is failling on windows')
    def test_show_settings(self):
        with new_dialog(MainDialog) as dlg:
            # Given home dialog
            dlg.pump_events()
            self.assertTrue(dlg.status_view.root.winfo_ismapped())
            self.assertFalse(dlg.settings_view.root.winfo_ismapped())
            # When invoking "Settings" button
            dlg.button_settings.invoke()
            dlg.pump_events()
            # Then settings view get displayed
            self.assertFalse(dlg.status_view.root.winfo_ismapped())
            self.assertTrue(dlg.settings_view.root.winfo_ismapped())
