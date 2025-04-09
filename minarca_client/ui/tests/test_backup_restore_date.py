# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
from minarca_client.core.backup import BackupInstance
from minarca_client.ui.backup_restore_date import BackupRestoreDate
from minarca_client.ui.dashboard import DashboardView
from minarca_client.ui.tests import BaseAppTest


class BackupRestoreDateTest(BaseAppTest):
    ACTIVE_VIEW = 'backup_restore_date.BackupRestoreDate'

    def setUp(self):
        super().setUp()
        # Given a local backup
        self.instance = instance = BackupInstance('1')
        self.instance.settings.remotehost = 'remotehost'
        self.instance.settings.remoteurl = 'http://localhost'
        self.instance.settings.repositoryname = 'test-repo'
        self.instance.settings.username = 'username'
        self.instance.settings.configured = True
        self.instance.settings.save()
        self.ACTIVE_VIEW_KWARGS = {'instance': instance}

    async def test_view(self):
        # Then the view get displayed.
        await self.pump_events()
        self.assertIsInstance(self.view, BackupRestoreDate)

    async def test_btn_cancel(self):
        # When user click on back or cancel button
        btn_cancel = self.view.ids.btn_cancel
        btn_cancel.dispatch('on_release')
        await self.pump_events()
        # Then view is updated
        self.assertIsInstance(self.view, DashboardView)

    async def test_disable(self):
        # Given a view.
        self.assertIsNotNone(self.view.parent)
        # When disabling or enabling
        self.view.disable = True
        await self.pump_events()
        self.view.disable = False
        await self.pump_events()
        # Then no error occur
