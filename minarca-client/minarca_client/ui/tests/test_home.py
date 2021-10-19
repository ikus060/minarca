'''
Created on Jul. 20, 2021

@author: ikus060
'''
import os
import tempfile
import tkinter
import unittest
from unittest.mock import MagicMock

from minarca_client.core.compat import IS_LINUX
from minarca_client.core.config import Status
from minarca_client.ui.home import HomeDialog

NO_DISPLAY = not os.environ.get('DISPLAY', False)


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
class HomeTest(unittest.TestCase):

    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        os.environ['MINARCA_CONFIG_HOME'] = self.tmp.name
        os.environ['MINARCA_DATA_HOME'] = self.tmp.name
        self.dlg = HomeDialog()

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()
        self.dlg.destroy()

    def pump_events(self):
        while self.dlg.root.dooneevent(tkinter._tkinter.ALL_EVENTS | tkinter._tkinter.DONT_WAIT):
            pass

    def test_last_backup_text(self):
        # Check value for each available status.
        for s in Status.LAST_RESULTS:
            self.dlg.status.data.lastresult = s
            value = self.dlg.status.last_backup_text(self.dlg.status.data)
            self.assertIsNotNone(value)

    def test_remote_text_undefined(self):
        self.dlg.status.data.remoteurl = None
        value = self.dlg.status.remote_text_tooltip(self.dlg.status.data)
        self.assertEqual('None @ None::None', value)

    def test_get_remote_text(self):
        context = self.dlg.status.data
        context['remoteurl'] = 'http://examples.com'
        context['username'] = 'user'
        context['remotehost'] = 'examples.com:2222'
        context['repositoryname'] = 'repo'
        value = self.dlg.status.remote_text_tooltip(self.dlg.status.data)
        self.assertEqual('user @ examples.com:2222::repo', value)

    def test_invoke_start_backup(self):
        # Given a Home dialog with a start_stop button
        self.pump_events()
        self.dlg.status.backup = MagicMock()
        self.assertIsNotNone(self.dlg.status.start_stop_button)
        # When invoking the button
        self.dlg.status.start_stop_button.invoke()
        # Then backup start
        self.dlg.status.backup.start.assert_called_once_with(force=True, fork=True)
