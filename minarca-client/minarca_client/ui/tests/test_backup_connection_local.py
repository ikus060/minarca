import asyncio
import os
import tempfile
import unittest

from minarca_client.core.backup import Backup
from minarca_client.core.compat import IS_LINUX
from minarca_client.ui.app import BackupConnectionLocal, MinarcaApp

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

    async def test_backup_connection_local(self):
        # Starting Minarca
        self.app = MinarcaApp(backup=Backup())
        asyncio.create_task(self.app.async_run())
        await asyncio.sleep(0)
        # When Browse to create local backup
        self.app.set_active_view('BackupConnectionLocal')
        await asyncio.sleep(0)
        # Then the view get displayed.
        view = self.app.root.ids.body.children[0]
        self.assertIsInstance(view, BackupConnectionLocal)
        # Then the view contains a default repository name
        self.assertNotEqual("", view.ids.repositoryname.text)
