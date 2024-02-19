import asyncio
import os
import tempfile
import unittest

from minarca_client.core.backup import Backup
from minarca_client.core.compat import IS_LINUX
from minarca_client.core.instance import BackupInstance
from minarca_client.ui.app import BackupCreate, DashboardView, MinarcaApp

NO_DISPLAY = not os.environ.get('DISPLAY', False)


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
class MainDialogTest(unittest.IsolatedAsyncioTestCase):
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

    async def test_default_dialog(self):
        # Given a non configure minarca
        self.dlg = MinarcaApp(backup=Backup())
        asyncio.get_event_loop().create_task(self.dlg.async_run())
        await asyncio.sleep(0)
        self.assertIsInstance(self.dlg.root.ids.body.children[0], BackupCreate)

    async def test_default_dialog_configured(self):
        # Given a configure minarca
        instance = BackupInstance('1')
        instance.settings.configured = True
        instance.settings.save()

        # Given a non configure minarca
        self.dlg = MinarcaApp(backup=Backup())
        asyncio.get_event_loop().create_task(self.dlg.async_run())
        await asyncio.sleep(0)
        self.assertIsInstance(self.dlg.root.ids.body.children[0], DashboardView)
