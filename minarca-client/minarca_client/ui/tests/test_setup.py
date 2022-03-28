'''
Created on Jul. 20, 2021

@author: ikus060
'''
import os
import tempfile
import tkinter
import unittest

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
        while self.dlg.root.dooneevent(tkinter._tkinter.ALL_EVENTS | tkinter._tkinter.DONT_WAIT):
            pass

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
