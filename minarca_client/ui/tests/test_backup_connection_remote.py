from unittest import mock

from minarca_client.core.instance import BackupInstance
from minarca_client.ui.app import BackupConnectionRemote, BackupCreate, BackupPatterns, DashboardView
from minarca_client.ui.tests import BaseAppTest


class BackupConnectionRemoteTest(BaseAppTest):
    ACTIVE_VIEW = 'BackupConnectionRemote'
    ACTIVE_VIEW_KWARGS = {'create': True}

    async def test_backup_connection_remote(self):
        # Then the view get displayed.
        self.assertIsInstance(self.view, BackupConnectionRemote)
        # Then the view contains a default repository name
        self.assertNotEqual("", self.view.ids.repositoryname.text)

    async def test_btn_cancel(self):
        # When user click on back or cancel button
        btn_cancel = self.view.ids.btn_cancel
        btn_cancel.dispatch('on_release')
        await self.pump_events()
        # Then view is updated
        self.assertIsInstance(self.view, BackupCreate)

    async def test_btn_next(self):

        def create_instance(*args, **kwargs):
            instance = self.view.backup._new_instance()
            instance.settings.remoteurl = 'https://example.com'
            instance.settings.username = 'admin'
            instance.settings.repositoryname = 'test'
            instance.settings.configured = True
            instance.settings.save()
            return instance

        # Given a mock to configure backup
        self.view.backup.configure_remote = mock_configure_remote = mock.AsyncMock(side_effect=create_instance)
        self.view.remoteurl = 'https://example.com'
        self.view.username = 'admin'
        self.view.password = 'admin123'
        # When user fill the form and click Next
        btn_next = self.view.ids.btn_next
        btn_next.dispatch('on_release')
        await self.pump_events()
        # Then a call was made
        mock_configure_remote.assert_called_once()
        # Then view is switch to next view
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

    async def test_edit_instance(self):
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
        # Then a test connection is running
        await self.view._test_connection_task
        # Then settings are gather from the instance
        self.assertEqual('test-repo', self.view.repositoryname)
        self.assertEqual('http://localhost', self.view.remoteurl)
        self.assertEqual('username', self.view.username)
        self.assertEqual('******', self.view.password)
        # When user click on back or cancel button
        btn_cancel = self.view.ids.btn_cancel
        btn_cancel.dispatch('on_release')
        await self.pump_events()
        # Then view is updated
        self.assertIsInstance(self.view, DashboardView)

    @mock.patch(
        'minarca_client.ui.backup_connection_remote.question_dialog', new_callable=mock.AsyncMock, return_value=True
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
        self.assertNotIsInstance(self.view, BackupConnectionRemote)
