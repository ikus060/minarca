import os
import tempfile
import tkinter
import unittest
from contextlib import contextmanager
from unittest import mock

from minarca_client.core.backup import Backup
from minarca_client.core.compat import IS_LINUX
from minarca_client.ui.backup_main import MainDialog
from minarca_client.ui.backup_create import BackupCreate

NO_DISPLAY = not os.environ.get('DISPLAY', False)


@contextmanager
def create_dialog():
    def pump_events():
        while dlg.root.dooneevent(tkinter._tkinter.ALL_EVENTS | tkinter._tkinter.DONT_WAIT):
            pass

    backup = Backup()
    dlg = MainDialog(backup=backup)
    dlg.set_active_view('BackupCreate')
    dlg.pump_events = pump_events
    try:
        yield dlg
    finally:
        dlg.pump_events()
        dlg.destroy()
        dlg.pump_events()


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
class BackupCreateTest(unittest.TestCase):

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

    def test_default_dialog(self):
        # Given a non configure minarca
        with create_dialog() as dlg:
            # When opening the main Dialog
            dlg.pump_events()
            # Then the creation dialog get displayed by default.
            self.assertIsInstance(dlg._last_view, BackupCreate)
            self.assertTrue(dlg._last_view.root.winfo_ismapped())
