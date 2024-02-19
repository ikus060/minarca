import asyncio
import os
from unittest import mock

from minarca_client.core.disk import DiskInfo
from minarca_client.core.instance import BackupInstance
from minarca_client.ui.app import BackupConnectionLocal, BackupCreate
from minarca_client.ui.tests import BaseAppTest

DISK_INFO = DiskInfo(
    device='/dev/sda1',
    mountpoint='/',
    relpath='tmp/tmp3p15kod6',
    caption='SAMSUNG MZVL2512HDJD-00BL2',
    free=14288068608,
    used=48573071360,
    size=66260148224,
    fstype='ext4',
    removable=False,
)


class BackupConnectionLocalTest(BaseAppTest):
    ACTIVE_VIEW = 'BackupConnectionLocal'

    async def test_backup_connection_local(self):
        # Then the view get displayed.
        self.assertIsInstance(self.view, BackupConnectionLocal)
        # Then the view contains a default repository name
        self.assertNotEqual("", self.view.ids.repositoryname.text)

    async def test_btn_cancel(self):
        # When user click on back or cancel button
        btn_cancel = self.view.ids.btn_cancel
        btn_cancel.dispatch('on_release')
        await self.pump_events()
        # Then view is updated
        self.assertIsInstance(self.view, BackupCreate)

    async def test_btn_refresh(self):
        # When user click on refresh, then disk list get refreshed.
        btn_refresh = self.view.ids.btn_refresh
        btn_refresh.dispatch('on_release')
        await self.pump_events()

    @mock.patch('minarca_client.ui.backup_connection_local.get_disk_info', return_value=DISK_INFO)
    @mock.patch('minarca_client.ui.backup_connection_local.folder_dialog', new_callable=mock.AsyncMock)
    async def test_select_custom_disk(self, mock_folder_dialog, mock_disk_info):
        # Mock disk selection
        mock_folder_dialog.return_value = self.tmp.name
        # When user click on "browser" then user can manually select a disk.
        self.view.ids.btn_browse.dispatch('on_release')
        # Then a task is created to select folder
        await self.view._select_custom_disk_task
        # Then a disk is selected
        self.assertEqual(self.view.selected_disk, DISK_INFO)

    async def test_btn_save(self):
        # Mock Backup instance
        self.view.backup = backup = mock.AsyncMock()
        repositoryname = self.view.repositoryname
        # Give a selected disk
        self.view.selected_disk = DISK_INFO
        # When user click save
        self.view.ids.btn_save.dispatch('on_release')
        try:
            await self.view._create_local_task
        except asyncio.CancelledError:
            pass
        # Then a backup is configured
        backup.configure_local.assert_called_once_with(
            path=os.path.join(DISK_INFO.mountpoint, DISK_INFO.relpath),
            repositoryname=repositoryname,
            force=False,
            instance=None,
        )

    async def test_disable(self):
        # Given a view.
        self.assertIsNotNone(self.view.parent)
        # When disabling or enabling
        self.view.disable = True
        await self.pump_events()
        self.view.disable = False
        await self.pump_events()
        # Then no error occur

    @mock.patch(
        'minarca_client.ui.backup_connection_local.question_dialog', new_callable=mock.AsyncMock, return_value=True
    )
    async def test_forget_instance(self, mock_question_dialog):
        # Given a remote backup instance
        self.instance = BackupInstance('1')
        self.instance.settings.remotehost = 'remotehost'
        self.instance.settings.remoteurl = 'http://localhost'
        self.instance.settings.repositoryname = 'test-repo'
        self.instance.settings.username = 'username'
        self.instance.settings.configured = True
        self.instance.settings.save()
        # When editing the settings
        self.app.set_active_view(self.ACTIVE_VIEW, create=False, instance=self.instance)
        # When user click on  forget instance button
        btn_forget = self.view.ids.btn_forget
        btn_forget.dispatch('on_release')
        await self.pump_events()
        # Then user is redirected to another view and the instance is deleted
        self.assertNotIsInstance(self.view, BackupConnectionLocal)
