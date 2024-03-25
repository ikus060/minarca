import asyncio
import os
import tempfile
import unittest

from minarca_client.core.backup import Backup, BackupInstance
from minarca_client.core.compat import IS_LINUX
from minarca_client.ui.app import BackupPatterns, BackupSettings, MinarcaApp

NO_DISPLAY = not os.environ.get('DISPLAY', False)


@unittest.skipIf(IS_LINUX and NO_DISPLAY, 'cannot run this without display')
class BackupSettingsTest(unittest.IsolatedAsyncioTestCase):
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

    async def asyncSetUp(self):
        # Given a local backup
        self.instance = instance = BackupInstance('1')
        instance.settings.configured = True
        instance.settings.save()
        # Starting Minarca
        self.app = MinarcaApp(backup=Backup())
        asyncio.create_task(self.app.async_run())
        await asyncio.sleep(0)
        # When Browse to create local backup
        self.app.set_active_view('BackupSettings', instance=instance, create=True)
        await asyncio.sleep(0)
        self.view = self.app.root.ids.body.children[0]

    async def test_view(self):
        # Then the view get displayed.
        self.assertIsInstance(self.view, BackupSettings)

    async def test_btn_cancel(self):
        # When user click on back or cancel button
        btn_cancel = self.view.ids.btn_cancel
        btn_cancel.dispatch('on_release')
        await asyncio.sleep(0)
        # Then view is updated
        self.view = self.app.root.ids.body.children[0]
        self.assertIsInstance(self.view, BackupPatterns)
