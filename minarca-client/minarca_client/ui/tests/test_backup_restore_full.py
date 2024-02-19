import datetime

from minarca_client.core.backup import BackupInstance
from minarca_client.ui.app import BackupRestoreDate, BackupRestoreFull
from minarca_client.ui.tests import BaseAppTest


class BackupRestoreFullTest(BaseAppTest):
    ACTIVE_VIEW = 'BackupRestoreFull'

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
        self.assertIsInstance(self.view, BackupRestoreFull)
        # Then wait for task to complete
        await self.view._fetch_filters_task

    async def test_btn_cancel(self):
        # Then wait for task to complete
        await self.view._fetch_filters_task
        # When user click on back or cancel button
        btn_cancel = self.view.ids.btn_cancel
        btn_cancel.dispatch('on_release')
        await self.pump_events()
        # Then view is updated
        self.assertIsInstance(self.view, BackupRestoreDate)
        self.assertEqual(self.view.restore_type, 'full')

    async def test_disable(self):
        # Then wait for task to complete
        await self.view._fetch_filters_task
        # Given a view.
        self.assertIsNotNone(self.view.parent)
        # When disabling or enabling
        self.view.disable = True
        await self.pump_events()
        self.view.disable = False
        await self.pump_events()
        # Then no error occur
