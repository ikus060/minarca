'''
Created on Jul. 20, 2021

@author: ikus060
'''
import asyncio
import os
import tempfile
import tkinter
import unittest
from unittest.mock import patch

from minarca_client.core.compat import IS_LINUX, IS_WINDOWS
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
        self.dlg.set_active_view('schedule')

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()
        self.dlg.destroy()

    def pump_events(self):
        asyncio.run(self.pump_events_async())

    async def pump_events_async(self):
        while self.dlg.root.dooneevent(tkinter._tkinter.ALL_EVENTS | tkinter._tkinter.DONT_WAIT):
            # Ignore `_watch_status_task`
            tasks = [
                t
                for t in asyncio.all_tasks()
                if 'StatusView._watch_status_task' not in str(t)
                if t != asyncio.current_task()
            ]
            await asyncio.gather(*tasks)

    def test_set_frequency_hourly(self):
        # Given a Schedule dialog
        self.pump_events()
        # When updating the frequency
        self.dlg.schedule_view.hourly_btn.invoke()
        self.pump_events()
        # Then the frequency is updated in configuration
        self.assertEqual(1, self.dlg.backup.get_settings('schedule'))

    def test_set_frequency_daily(self):
        # Given a Schedule dialog
        self.pump_events()
        # When updating the frequency
        self.dlg.schedule_view.daily_btn.invoke()
        self.pump_events()
        # Then the frequency is updated in configuration
        self.assertEqual(24, self.dlg.backup.get_settings('schedule'))

    def test_set_frequency_twice(self):
        # Given a Schedule dialog
        self.pump_events()
        # When updating the frequency
        self.dlg.schedule_view.twice_btn.invoke()
        self.pump_events()
        # Then the frequency is updated in configuration
        self.assertEqual(12, self.dlg.backup.get_settings('schedule'))

    @patch("tkinter.messagebox.showwarning")
    @patch("minarca_client.ui.schedule.CredentialDialog")
    @unittest.skipUnless(IS_WINDOWS, reason="feature only supported on Windows")
    def test_run_if_logged_out(self, mock_dlg, mock_showwarning):
        # Given a mocked credential dialog
        mock_dlg.data.return_value = dict(username='test', password='invalid')
        # Given a Schedule dialog
        self.pump_events()
        # When updating the frequency
        self.dlg.schedule_view.run_if_logged_out_btn.invoke()
        self.pump_events()
        # Then error is raised and displayed to user
        mock_showwarning.assert_called_once()
