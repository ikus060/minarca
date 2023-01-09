'''
Created on Jul. 20, 2021

@author: ikus060
'''
import asyncio
import os
import tempfile
import tkinter
import unittest
from unittest.mock import ANY, MagicMock

from minarca_client.core import RepositoryNameExistsError
from minarca_client.core.compat import IS_LINUX
from minarca_client.ui.setup import SetupDialog

NO_DISPLAY = not os.environ.get('DISPLAY', False)


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
class SetupTest(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.tmp = tempfile.TemporaryDirectory()
        os.chdir(self.tmp.name)
        os.environ['MINARCA_CONFIG_HOME'] = self.tmp.name
        os.environ['MINARCA_DATA_HOME'] = self.tmp.name
        self.dlg = SetupDialog()

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()
        self.dlg.destroy()

    def pump_events(self):
        asyncio.run(self.pump_events_async())

    async def pump_events_async(self):
        while self.dlg.root.dooneevent(tkinter._tkinter.ALL_EVENTS | tkinter._tkinter.DONT_WAIT):
            await asyncio.gather(*asyncio.all_tasks() - {asyncio.current_task()})

    def test_valid_form_with_default_value(self):
        # Given default configuration.
        # When opening the Setup dialog
        self.pump_events()
        # Then form is not valid.
        self.assertFalse(self.dlg.data.valid_form)
        self.assertEqual('', self.dlg.data.username)
        self.assertFalse(self.dlg.data.username_valid)
        self.assertEqual('', self.dlg.data.password)
        self.assertFalse(self.dlg.data.password_valid)
        self.assertEqual('', self.dlg.data.remoteurl)
        self.assertFalse(self.dlg.data.remoteurl_valid)
        self.assertTrue(self.dlg.data.repository_name)
        self.assertTrue(self.dlg.data.repository_name_valid)
        # Then submit button is disabled
        self.assertEqual(self.dlg.submitbutton.state(), ('disabled',))

    def test_valid_form_with_valid_values(self):
        # Given valid values provided by user
        self.dlg.data.username = 'test'
        self.dlg.data.password = 'test'
        self.dlg.data.remoteurl = 'http://examples.com'
        self.pump_events()
        # When dialog get updated.
        self.pump_events()
        # Then form is valid.
        self.assertTrue(self.dlg.data.valid_form)
        self.assertTrue(self.dlg.data.username_valid)
        self.assertTrue(self.dlg.data.password_valid)
        self.assertTrue(self.dlg.data.remoteurl_valid)
        # Then submit button is enabled
        self.assertEqual(self.dlg.submitbutton.state(), tuple())

    def test_submit_form(self):
        self.dlg.close = MagicMock()
        self.dlg.backup.link = MagicMock()
        # Given a form with valid value
        self.dlg.data.username = 'test'
        self.dlg.data.password = 'test'
        self.dlg.data.remoteurl = 'http://examples.com'
        self.pump_events()
        # When user click "submit"
        self.dlg.root.after(0, lambda: self.dlg.submitbutton.invoke())
        self.pump_events()
        # Then link() get called
        self.dlg.backup.link.assert_called_once_with(
            remoteurl='http://examples.com', username='test', password='test', repository_name=ANY, force=False
        )
        # Then close() get called
        self.dlg.close.assert_called_once()

    def test_submit_form_with_already_exists(self):
        self.dlg.close = MagicMock()
        # Given an exception raised when linking
        self.dlg.backup.link = MagicMock(side_effect=RepositoryNameExistsError)
        # Given the user press "Yes"
        tkinter.messagebox.askyesno = MagicMock(return_value=True)
        # Given a form with valid value
        self.dlg.data.username = 'test'
        self.dlg.data.password = 'test'
        self.dlg.data.remoteurl = 'http://examples.com'
        self.pump_events()
        # When user click "submit"
        self.dlg.root.after(0, lambda: self.dlg.submitbutton.invoke())
        self.pump_events()
        # Then link() get called a first time with force=False
        self.dlg.backup.link.assert_any_call(
            remoteurl='http://examples.com', username='test', password='test', repository_name=ANY, force=False
        )
        # Then link() get called a second time with force=False
        self.dlg.backup.link.assert_any_call(
            remoteurl='http://examples.com', username='test', password='test', repository_name=ANY, force=True
        )
        # Then close() is not called
        self.dlg.close.assert_not_called()
