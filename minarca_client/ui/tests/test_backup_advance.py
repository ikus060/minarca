# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
from minarca_client.ui.backup_advance import BackupAdvanceSettings
from minarca_client.ui.dashboard import DashboardView
from minarca_client.ui.tests import BaseAppTest


class BackupAdvanceSettingsTest(BaseAppTest):
    ACTIVE_VIEW = 'backup_advance.BackupAdvanceSettings'

    def setup_backup(self):
        backup = super().setup_backup()
        # Given a local backup
        self.instance = instance = backup._new_instance()
        instance.settings.configured = True
        instance.save_settings()
        self.ACTIVE_VIEW_KWARGS = {'instance': instance, 'create': True}
        return backup

    async def test_view(self):
        # Then the view get displayed.
        self.assertIsInstance(self.view, BackupAdvanceSettings)

    async def test_btn_cancel(self):
        # When user click on back or cancel button
        btn_cancel = self.view.ids.btn_cancel
        btn_cancel.dispatch('on_release')
        await self.pump_events()
        # Then view is updated
        self.assertIsInstance(self.view, DashboardView)

    async def test_btn_save(self):
        # Given the user enter new commands
        self.view.pre_hook_command = "echo foo"
        self.view.ignore_hook_errors = True
        # When user click save
        btn_save = self.view.ids.btn_save
        btn_save.dispatch('on_release')
        await self.pump_events()
        # Then view is updated
        self.assertIsInstance(self.view, DashboardView)
        # Then the command is save into the settings
        self.assertEqual(self.instance.settings.pre_hook_command, "echo foo")
        self.assertTrue(self.instance.settings.ignore_hook_errors)
