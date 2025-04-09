# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
from minarca_client.core.backup import BackupInstance, Patterns
from minarca_client.ui.backup_create import BackupCreate
from minarca_client.ui.backup_patterns import BackupPatterns
from minarca_client.ui.tests import BaseAppTest


class BackupPatternsTest(BaseAppTest):
    ACTIVE_VIEW = 'backup_patterns.BackupPatterns'

    def setUp(self):
        super().setUp()
        # Given a local backup
        self.instance = instance = BackupInstance('1')
        instance.settings.configured = True
        instance.settings.save()
        # With patterns
        instance.patterns.extend(Patterns.defaults())
        instance.patterns.save()
        self.ACTIVE_VIEW_KWARGS = {'instance': instance, 'create': True}

    async def test_view(self):
        # Then the view get displayed.
        self.assertIsInstance(self.view, BackupPatterns)

    async def test_btn_cancel(self):
        # When user click on back or cancel button
        btn_cancel = self.view.ids.btn_cancel
        btn_cancel.dispatch('on_release')
        await self.pump_events()
        # Then view is updated
        self.assertIsInstance(self.view, BackupCreate)

    async def test_disable(self):
        # Given a view.
        self.assertIsNotNone(self.view.parent)
        # When disabling or enabling
        self.view.disable = True
        await self.pump_events()
        self.view.disable = False
        await self.pump_events()
        # Then no error occur
