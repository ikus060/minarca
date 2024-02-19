import asyncio
import time

from minarca_client.core.backup import BackupInstance
from minarca_client.ui.app import BackupLogs, DashboardView
from minarca_client.ui.tests import BaseAppTest


class BackupLogsTest(BaseAppTest):
    ACTIVE_VIEW = 'BackupLogs'

    def setUp(self):
        super().setUp()
        # Given a local backup
        self.instance = instance = BackupInstance('1')
        instance.settings.configured = True
        instance.settings.save()
        self.ACTIVE_VIEW_KWARGS = {'instance': instance}

    async def test_update_logs(self):
        # Given user display backup logs
        self.assertIsInstance(self.view, BackupLogs)
        # When backup action get trigger and write to logs
        status = self.instance.status
        status.action = 'backup'
        status.lastdate = int(time.time())
        status.save()
        with open(self.instance.backup_log_file, 'w+') as f:
            f.write('first line of logs\n')
            f.write('second line of text\n')
        # Then the view get updated (within 2 sec) with 2 lines of text.
        await self.pump_events()
        await asyncio.sleep(2)
        self.assertEqual(len(self.view.lines), 2)
        # Cleanup
        _readlogs_task = self.view._readlogs_task
        self.app.set_active_view('DashboardView')
        try:
            await _readlogs_task
        except asyncio.CancelledError:
            pass

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
