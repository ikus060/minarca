'''
Created on Jul. 20, 2021

@author: ikus060
'''
import os
import tempfile
import time
import tkinter
import unittest
from unittest.mock import MagicMock

from minarca_client.core.compat import IS_LINUX
from minarca_client.ui.home import HomeDialog

NO_DISPLAY = not os.environ.get('DISPLAY', False)


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
class SettingsTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        os.environ['MINARCA_CONFIG_HOME'] = self.tmp.name
        os.environ['MINARCA_DATA_HOME'] = self.tmp.name
        os.environ['MINARCA_CHECK_LATEST_VERSION'] = 'False'
        self.dlg = HomeDialog()
        self.dlg.set_active_view('settings')

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()
        self.dlg.destroy()

    def pump_events(self):
        while self.dlg.root.dooneevent(tkinter._tkinter.ALL_EVENTS | tkinter._tkinter.DONT_WAIT):
            pass

    def test_toggle_check_latest_version(self):
        # Given a Settings dialog
        self.pump_events()
        self.assertEqual(True, self.dlg.backup.get_settings('check_latest_version'))
        self.assertEqual(('selected',), self.dlg.settings_view.check_latest_version_toggle_button.state())
        # When user click on check_latest_version toggle button
        self.dlg.settings_view.check_latest_version_toggle_button.invoke()
        self.pump_events()
        # Then Option is updated in settings.
        self.assertEqual(False, self.dlg.backup.get_settings('check_latest_version'))
        self.assertEqual(tuple(), self.dlg.settings_view.check_latest_version_toggle_button.state())
        # When cliking again on the button
        self.dlg.settings_view.check_latest_version_toggle_button.invoke()
        self.pump_events()
        # Then option is updated in settings.
        self.assertEqual(True, self.dlg.backup.get_settings('check_latest_version'))
        self.assertEqual(('selected',), self.dlg.settings_view.check_latest_version_toggle_button.state())

    def test_check_latest_version(self):
        self.dlg.settings_view.latest_check = MagicMock()
        # Given a Settings dialog
        self.pump_events()
        # When user click on "Check for update"
        self.dlg.settings_view.check_latest_version_button.invoke()
        self.pump_events()
        # Then
        time.sleep(1)
        self.dlg.settings_view.latest_check.is_latest.assert_called_once()
