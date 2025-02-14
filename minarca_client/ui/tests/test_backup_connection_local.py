import asyncio
import shutil
import tempfile
from pathlib import Path
from unittest import mock

from minarca_client.core.disk import LocationInfo, get_location_info
from minarca_client.core.instance import BackupInstance
from minarca_client.core.tests.test_instance import remove_readonly
from minarca_client.ui.backup_connection_local import BackupConnectionLocal
from minarca_client.ui.backup_create import BackupCreate
from minarca_client.ui.backup_patterns import BackupPatterns
from minarca_client.ui.dashboard import DashboardView
from minarca_client.ui.tests import BaseAppTest

DISK_INFO = LocationInfo(
    mountpoint=Path('/'),
    relpath=Path('tmp/tmp3p15kod6'),
    caption='SAMSUNG MZVL2512HDJD-00BL2',
    free=14288068608,
    used=48573071360,
    size=66260148224,
    fstype='ext4',
    device_type=LocationInfo.FIXED,
)


class BackupConnectionLocalTest(BaseAppTest):
    ACTIVE_VIEW = 'backup_connection_local.BackupConnectionLocal'

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
        # Given a local backup instance that doesn't exists
        self.instance = BackupInstance('1')
        self.instance.settings.localuuid = 'e347e062-0912-48f9-a211-12dbe97b1f13'
        self.instance.settings.localrelpath = 'minarca/my-desktop'
        self.instance.settings.localmountpoint = '/media/7DBC7A0C46439F04'
        self.instance.settings.localcaption = 'Generic Mass Storage'
        self.instance.settings.repositoryname = 'test-repo'
        self.instance.settings.configured = True
        self.instance.settings.save()
        # When editing the settings
        self.app.set_active_view(self.ACTIVE_VIEW, create=False, instance=self.instance)
        # When user click on refresh, then disk list get refreshed.
        btn_refresh = self.view.ids.btn_refresh
        btn_refresh.dispatch('on_release')
        await self.pump_events()

    @mock.patch('minarca_client.ui.backup_connection_local.get_location_info', return_value=DISK_INFO)
    @mock.patch('minarca_client.ui.backup_connection_local.folder_dialog', new_callable=mock.AsyncMock)
    async def test_select_custom_location(self, mock_folder_dialog, mock_disk_info):
        # Mock disk selection
        mock_folder_dialog.return_value = self.tmp.name
        # When user click on "browser" then user can manually select a disk.
        self.view.ids.btn_browse.dispatch('on_release')
        # Then a task is created to select folder
        await self.view._select_custom_location_task
        # Then a disk is selected
        self.assertEqual(self.view.selected_location, DISK_INFO)

    async def test_btn_save(self):
        # Given a local backup instance already exists.
        self.instance = BackupInstance('1')
        self.instance.settings.localuuid = 'e347e062-0912-48f9-a211-12dbe97b1f13'
        self.instance.settings.localrelpath = 'minarca/my-desktop'
        self.instance.settings.localmountpoint = '/media/7DBC7A0C46439F04'
        self.instance.settings.localcaption = 'Generic Mass Storage'
        self.instance.settings.repositoryname = 'test-repo'
        self.instance.settings.configured = True
        self.instance.settings.save()
        await self.view._refresh_locations_task
        # Mock Backup instance
        self.view.backup = backup = mock.AsyncMock()
        repositoryname = self.view.repositoryname
        # Give a selected disk
        self.view.selected_location = DISK_INFO
        # When user click save
        self.view.ids.btn_save.dispatch('on_release')
        try:
            await self.view._create_local_task
        except asyncio.CancelledError:
            pass
        # Then a backup is configured
        backup.configure_local.assert_called_once_with(
            path=DISK_INFO.mountpoint / DISK_INFO.relpath,
            repositoryname=repositoryname,
            force=False,
            instance=None,
        )
        # Then user is redirected to Dashboard
        self.assertIsInstance(self.view, DashboardView)

    async def test_btn_save_with_create(self):
        tempdir = tempfile.mkdtemp(prefix='minarca-client-test')
        try:
            # Given the view is in create mode.
            self.app.set_active_view(self.ACTIVE_VIEW, create=True)
            await self.view._refresh_locations_task
            # Mock Backup instance
            self.view.repositoryname = 'testing'
            # Give a selected disk
            self.view.selected_location = get_location_info(Path(tempdir))
            # When user click save
            self.view.ids.btn_save.dispatch('on_release')
            try:
                await self.view._create_local_task
            except asyncio.CancelledError:
                pass
            # Then user is redirect to next view.
            self.assertIsInstance(self.view, BackupPatterns)
            # Then a backup is configured
            self.assertIsNotNone(self.view.instance)
        finally:
            shutil.rmtree(tempdir, onerror=remove_readonly)

    async def test_disable(self):
        # Given a view.
        self.assertIsNotNone(self.view.parent)
        # When disabling or enabling
        self.view.disable = True
        await self.pump_events()
        self.view.disable = False
        await self.pump_events()
        # Then no error occur

    async def test_with_local_destination_not_found(self):
        # Given a local backup instance that doesn't exists
        self.instance = BackupInstance('1')
        self.instance.settings.localuuid = 'e347e062-0912-48f9-a211-12dbe97b1f13'
        self.instance.settings.localrelpath = 'minarca/my-desktop'
        self.instance.settings.localmountpoint = '/media/7DBC7A0C46439F04'
        self.instance.settings.localcaption = 'Generic Mass Storage'
        self.instance.settings.repositoryname = 'test-repo'
        self.instance.settings.configured = True
        self.instance.settings.save()
        # When editing the settings
        self.app.set_active_view(self.ACTIVE_VIEW, create=False, instance=self.instance)
        await self.pump_events()
        # Then view get displayed with local destination.
        await self.view._refresh_locations_task
        self.assertIsNotNone(self.view.selected_location)
        # Then disk size is not repported
        self.assertIsNone(self.view.selected_location.free)
        self.assertIsNone(self.view.selected_location.used)
        self.assertIsNone(self.view.selected_location.size)

    async def test_with_existing_location(self):
        # Given a local backup
        tempdir = tempfile.mkdtemp(prefix='minarca-client-test')
        try:
            self.instance = await self.view.backup.configure_local(tempdir, repositoryname='test-repo')
            # When editing the settings
            self.app.set_active_view(self.ACTIVE_VIEW, create=False, instance=self.instance)
            await self.pump_events()
            # Then view get displayed with local destination.
            await self.view._refresh_locations_task
            self.assertIsNotNone(self.view.selected_location)
            # Then disk size is repported
            self.assertIsNotNone(self.view.selected_location.free)
            self.assertIsNotNone(self.view.selected_location.used)
            self.assertIsNotNone(self.view.selected_location.size)
        finally:
            shutil.rmtree(tempdir, onerror=remove_readonly)

    @mock.patch(
        'minarca_client.ui.backup_connection_local.question_dialog', new_callable=mock.AsyncMock, return_value=True
    )
    async def test_forget_instance(self, mock_question_dialog):
        # Given a local backup instance
        self.instance = BackupInstance('1')
        self.instance.settings.localuuid = 'e347e062-0912-48f9-a211-12dbe97b1f13'
        self.instance.settings.localrelpath = 'minarca/my-desktop'
        self.instance.settings.localmountpoint = '/media/7DBC7A0C46439F04'
        self.instance.settings.localcaption = 'Generic Mass Storage'
        self.instance.settings.repositoryname = 'test-repo'
        self.instance.settings.configured = True
        self.instance.settings.save()
        # When editing the settings
        self.app.set_active_view(self.ACTIVE_VIEW, create=False, instance=self.instance)
        await self.pump_events()
        # When user click on forget instance button
        btn_forget = self.view.ids.btn_forget
        btn_forget.dispatch('on_release')
        await self.pump_events()
        # Then user is redirected to another view and the instance is deleted
        self.assertNotIsInstance(self.view, BackupConnectionLocal)
