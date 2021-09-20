'''
Created on Jul. 20, 2021

@author: ikus060
'''
import unittest
from minarca_client.ui.home import HomeDialog
from minarca_client.core.config import Status
import os
import tempfile


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

    def test_get_last_backup_text(self):
        # Check value for each available status.
        for s in Status.LAST_RESULTS:
            status = self.dlg.backup.get_status()
            status['lastresult'] = s
            status.save()
            value = self.dlg._get_last_backup_text()
            self.assertIsNotNone(value)

    def test_get_remote_text_undefined(self):
        settings = self.dlg.backup.get_settings()
        if 'remoteurl' in settings:
            del settings['remoteurl']
        settings.save()
        self.assertEqual(('None', 'None @ None::None'),
                         self.dlg._get_remote_text())

    def test_get_remote_text(self):
        settings = self.dlg.backup.get_settings()
        settings['remoteurl'] = 'http://examples.com'
        settings['username'] = 'user'
        settings['remotehost'] = 'examples.com:2222'
        settings['repositoryname'] = 'repo'
        settings.save()
        self.assertEqual(('http://examples.com', 'user @ examples.com:2222::repo'),
                         self.dlg._get_remote_text())
