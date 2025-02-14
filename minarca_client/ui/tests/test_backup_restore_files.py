import datetime
import os
import shutil
import tempfile

from minarca_client.core.backup import Backup, BackupInstance
from minarca_client.core.compat import IS_MAC
from minarca_client.core.pattern import Pattern
from minarca_client.core.tests.test_instance import remove_readonly
from minarca_client.ui.backup_restore_date import BackupRestoreDate
from minarca_client.ui.backup_restore_files import BackupRestoreFiles
from minarca_client.ui.tests import BaseAppTest


class BackupRestoreFilesTest(BaseAppTest):
    ACTIVE_VIEW = 'backup_restore_files.BackupRestoreFiles'

    def setUp(self):
        super().setUp()
        # Given a local backup
        self.instance = instance = BackupInstance('1')
        self.instance.settings.remotehost = 'remotehost'
        self.instance.settings.remoteurl = 'http://localhost'
        self.instance.settings.repositoryname = 'test-repo'
        self.instance.settings.username = 'username'
        self.instance.settings.configured = True
        instance.settings.configured = True
        instance.settings.save()
        self.ACTIVE_VIEW_KWARGS = {'instance': instance, 'increment': datetime.datetime.now()}

    async def test_view(self):
        # Then the view get displayed.
        self.assertIsInstance(self.view, BackupRestoreFiles)

    async def test_btn_cancel(self):
        # When user click on back or cancel button
        btn_cancel = self.view.ids.btn_cancel
        btn_cancel.dispatch('on_release')
        await self.pump_events()
        # Then view is updated
        self.assertIsInstance(self.view, BackupRestoreDate)

    async def test_disable(self):
        # Given a view.
        self.assertIsNotNone(self.view.parent)
        # When disabling or enabling
        self.view.disable = True
        await self.pump_events()
        self.view.disable = False
        await self.pump_events()
        # Then no error occur


class BackupRestoreFilesTest2(BaseAppTest):
    ACTIVE_VIEW = 'backup_restore_files.BackupRestoreFiles'

    async def asyncSetUp(self):
        # Given a backup with local destination
        self.tempdir = tempfile.mkdtemp(prefix='minarca-client-test')
        self.instance = await Backup().configure_local(self.tempdir, repositoryname='test-repo')
        patterns = self.instance.patterns
        patterns.clear()
        patterns.append(Pattern(True, os.path.realpath(self.tmp.name), None))
        patterns.save()
        # when running backup
        await self.instance.backup(force=True)

        # Given a local backup
        self.ACTIVE_VIEW_KWARGS = {'instance': self.instance, 'increment': datetime.datetime.now()}

        # Open View.
        await super().asyncSetUp()

    def tearDown(self):
        shutil.rmtree(self.tempdir, onerror=remove_readonly)
        return super().tearDown()

    async def test_filter(self):
        # Given a view.
        self.assertIsNotNone(self.view.parent)
        await self.pump_events()
        # Then the view is featching list of files.
        self.assertIsNotNone(self.view._fetch_files_task)
        await self.view._fetch_files_task
        # Then the list of items is not empty
        self.assertTrue(self.view.file_items)
        # When user select an item.
        await self.pump_events()
        rv = self.view.ids.availables.children[0]
        # Then an item is selected
        # This part is always failing in CICD pipeline while working on real MacOS.
        # So let skip this part for now.
        if not IS_MAC:
            file_item = rv.children[3]
            file_item.toggle_checkbox_state()
            self.assertEqual(self.view.selected_files, [file_item.data])
