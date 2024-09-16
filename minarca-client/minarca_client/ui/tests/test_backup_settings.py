import asyncio
from unittest import mock

import responses

from minarca_client.core.backup import BackupInstance
from minarca_client.core.minarcaid import ssh_keygen
from minarca_client.ui.app import BackupPatterns, BackupSettings, DashboardView
from minarca_client.ui.tests import BaseAppTest


class BackupSettingsTest(BaseAppTest):
    ACTIVE_VIEW = 'BackupSettings'

    def setUp(self):
        super().setUp()
        # Given a local backup
        self.instance = instance = BackupInstance('1')
        instance.settings.configured = True
        instance.settings.save()
        self.ACTIVE_VIEW_KWARGS = {'instance': instance, 'create': True}

    async def test_view(self):
        # Then the view get displayed.
        self.assertIsInstance(self.view, BackupSettings)

    async def test_edit_and_save_local(self):
        # Given a backup configured
        self.instance.settings.maxage = 1
        self.instance.settings.keepdays = 2
        self.instance.settings.ignore_weekday = [5, 6]
        self.instance.settings.schedule = 12
        self.instance.settings.save()
        # When editing the backup settings
        self.app.set_active_view('BackupSettings', instance=self.instance, create=False)
        await asyncio.sleep(0)
        # Then the view get displayed
        self.assertIsInstance(self.view, BackupSettings)
        # When making modification and saving
        self.view.maxage = 15
        self.view.keepdays = 30
        self.view.schedule = 1
        self.view.ids.btn_save.dispatch('on_release')
        try:
            await self.view._save_task
        except asyncio.CancelledError:
            pass
        # Then modification are saved
        self.assertEqual(self.instance.settings.maxage, 15)
        self.assertEqual(self.instance.settings.keepdays, 30)
        self.assertEqual(self.instance.settings.schedule, 1)
        # The dashboard view is displayed
        self.assertIsInstance(self.view, DashboardView)
        # Then make sure schedule get created
        self.assertTrue(self.app.backup.scheduler.exists())

    @responses.activate
    async def test_edit_and_save_remote(self):
        responses.add(responses.GET, "http://localhost/api/")
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/",
            json={
                'email': 'admin@example.com',
                'username': 'admin',
                'repos': [{'name': 'test-repo'}],
                'disk_quota': 1234,
                'disk_usage': 123,
            },
        )
        responses.add(
            responses.GET,
            "http://localhost/api/currentuser/repos/test-repo",
            json={'maxage': 12, 'keepdays': 34, 'ignore_weekday': [5, 6]},
        )
        responses.add(
            responses.POST,
            "http://localhost/api/currentuser/repos/test-repo",
        )
        # Given a remote backup configured
        self.instance.settings.remotehost = 'remotehost'
        self.instance.settings.remoteurl = 'http://localhost'
        self.instance.settings.repositoryname = 'test-repo'
        self.instance.settings.username = 'username'
        self.instance.settings.maxage = 1
        self.instance.settings.keepdays = 2
        self.instance.settings.ignore_weekday = [5, 6]
        self.instance.settings.schedule = 12
        self.instance.settings.save()
        ssh_keygen(self.instance.public_key_file, self.instance.private_key_file)
        self.assertTrue(self.instance.is_remote())
        # When editing the backup settings
        self.app.set_active_view('BackupSettings', instance=self.instance, create=False)
        # Then the view get displayed
        self.assertIsInstance(self.view, BackupSettings)
        # Then a task is started to load settings remotely
        self.assertIsNotNone(self.view._load_task, 'expecting a task to be created to load remote settings')
        await self.view._load_task
        # When making modification and saving
        self.view.maxage = 15
        self.view.keepdays = 30
        self.view.schedule = 1
        self.view.ids.btn_save.dispatch('on_release')
        try:
            await self.view._save_task
        except asyncio.CancelledError:
            pass
        # Then modification are saved
        self.assertEqual(self.instance.settings.maxage, 15)
        self.assertEqual(self.instance.settings.keepdays, 30)
        self.assertEqual(self.instance.settings.schedule, 1)
        # The dashboard view is displayed
        self.assertIsInstance(self.view, DashboardView)
        # The settings was pushed to remote server
        responses.assert_call_count("http://localhost/api/currentuser/repos/test-repo", 2)
        # For better statility of the test - let stop the long waiting task.
        task = self.view.ids.card_list.children[0]._test_connection_task
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        # Then make sure schedule get created
        self.assertTrue(self.app.backup.scheduler.exists())

    async def test_btn_cancel(self):
        # When user click on back or cancel button
        btn_cancel = self.view.ids.btn_cancel
        btn_cancel.dispatch('on_release')
        await asyncio.sleep(0)
        # Then view is updated
        self.assertIsInstance(self.view, BackupPatterns)

    async def test_disable(self):
        # Given a view.
        self.assertIsNotNone(self.view.parent)
        # When disabling or enabling
        self.view.disable = True
        await self.pump_events()
        self.view.disable = False
        await self.pump_events()
        # Then no error occur

    @mock.patch('minarca_client.ui.backup_settings.question_dialog', new_callable=mock.AsyncMock, return_value=True)
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
        self.assertNotIsInstance(self.view, BackupSettings)
