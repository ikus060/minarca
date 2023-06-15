'''
Created on Jul. 20, 2021

@author: ikus060
'''
import os
import tempfile
import tkinter
import unittest
from contextlib import contextmanager
from unittest.mock import MagicMock

from minarca_client.core.compat import IS_LINUX
from minarca_client.core.config import Status
from minarca_client.ui.home import HomeDialog

NO_DISPLAY = not os.environ.get('DISPLAY', False)


@contextmanager
def home_dialog():
    cwd = os.getcwd()
    tmp = tempfile.TemporaryDirectory()
    os.chdir(tmp.name)
    os.environ['MINARCA_CONFIG_HOME'] = tmp.name
    os.environ['MINARCA_DATA_HOME'] = tmp.name
    os.environ['MINARCA_CHECK_LATEST_VERSION'] = 'False'

    def pump_events():
        while dlg.root.dooneevent(tkinter._tkinter.ALL_EVENTS | tkinter._tkinter.DONT_WAIT):
            pass

    dlg = HomeDialog()
    dlg.pump_events = pump_events
    dlg.set_active_view('settings')
    dlg.pump_events()
    try:
        yield dlg
    finally:
        dlg.destroy()
        dlg.pump_events()
        os.chdir(cwd)
        tmp.cleanup()


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
class StatusViewTest(unittest.TestCase):
    def test_last_backup_text(self):
        with home_dialog() as dlg:
            # Check value for each available status.
            for s in Status.LAST_RESULTS:
                dlg.status_view.data.lastresult = s
                value = dlg.status_view.last_backup_text(dlg.status_view.data)
                self.assertIsNotNone(value)

    def test_remote_text_undefined(self):
        with home_dialog() as dlg:
            dlg.status_view.data.remoteurl = None
            value = dlg.status_view.remote_text_tooltip(dlg.status_view.data)
            self.assertEqual('None @ None::None', value)

    def test_get_remote_text(self):
        with home_dialog() as dlg:
            context = dlg.status_view.data
            context['remoteurl'] = 'http://examples.com'
            context['username'] = 'user'
            context['remotehost'] = 'examples.com:2222'
            context['repositoryname'] = 'repo'
            value = dlg.status_view.remote_text_tooltip(dlg.status_view.data)
            self.assertEqual('user @ examples.com:2222::repo', value)

    def test_invoke_start_backup(self):
        with home_dialog() as dlg:
            # Given a Home dialog with a start_stop button
            dlg.pump_events()
            dlg.status_view.backup = MagicMock()
            self.assertIsNotNone(dlg.status_view.start_stop_button)
            # When invoking the button
            dlg.status_view.start_stop_button.invoke()
            # Then backup start
            dlg.status_view.backup.start.assert_called_once_with(force=True)
