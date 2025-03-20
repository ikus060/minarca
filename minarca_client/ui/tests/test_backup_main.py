import asyncio
import datetime

from parameterized import parameterized

from minarca_client.core.instance import BackupInstance
from minarca_client.core.status import Datetime
from minarca_client.ui.backup_card import BackupCard
from minarca_client.ui.backup_create import BackupCreate
from minarca_client.ui.dashboard import DashboardView
from minarca_client.ui.tests import BaseAppTest


class MainDialogTest(BaseAppTest):
    async def test_default_dialog(self):
        # When no backup configure. Then BackupCreate is displayed by default.
        self.assertIsInstance(self.view, BackupCreate)

    async def test_disable(self):
        # Given a view.
        self.assertIsNotNone(self.view.parent)
        # When disabling or enabling
        self.app.root.disable = True
        self.app.root.disable = False
        # Then no error occur
        # Then not error occur.


class MainDialogWithBackupTest(BaseAppTest):
    def setUp(self):
        super().setUp()
        # Given a local backup
        self.instance = instance = BackupInstance('1')
        instance.settings.configured = True
        instance.settings.save()
        self.ACTIVE_VIEW_KWARGS = {'instance': instance}

    async def test_default_dialog(self):
        # When backup is configure. Then BackupCreate is displayed by default.
        self.assertIsInstance(self.view, DashboardView)

    async def test_backup_card_update_status(self):
        # Given a dialog display current backup within a card.
        self.assertIsInstance(self.view, DashboardView)
        card = self.view.ids.card_list.children[0]
        self.assertIsInstance(card, BackupCard)
        initial_status = dict(card.status._data)
        # When Status of instance get updated
        t = self.instance.status
        t.lastresult = 'SUCCESS'
        t.lastsuccess = Datetime()
        t.lastdate = t.lastsuccess
        t.save()
        await asyncio.sleep(1)
        await self.pump_events()
        # Then status get reloaded
        new_status = dict(card.status._data)
        self.assertNotEqual(initial_status, new_status)

    async def test_backup_card_update_settings(self):
        # Given a dialog display current backup within a card.
        self.assertIsInstance(self.view, DashboardView)
        card = self.view.ids.card_list.children[0]
        self.assertIsInstance(card, BackupCard)
        initial_settings = dict(card.settings._data)
        # When Status of instance get updated
        t = self.instance.settings
        t.pause_until = Datetime() + datetime.timedelta(hours=1)
        t.save()
        await asyncio.sleep(1)
        await self.pump_events()
        # Then settings get reloaded
        new_settings = dict(card.settings._data)
        self.assertNotEqual(initial_settings, new_settings)

    @parameterized.expand(
        [
            ('backup_logs', 'BackupLogs'),
            ('backup_connection', 'BackupConnectionLocal'),
            ('backup_settings', 'BackupSettings'),
            ('backup_patterns', 'BackupPatterns'),
            ('backup_restore', 'BackupRestoreDate'),
            ('backup_advance', 'BackupAdvanceSettings'),
        ]
    )
    async def test_switch_view(self, fname, expected_view):
        # Given user click on buttons (simulated by function call)
        card_view = self.view.ids.card_list.children[0]
        func = getattr(card_view, fname)
        func()
        await self.pump_events()
        # Then view is updated
        self.assertEqual(self.view.__class__.__name__, expected_view)

    async def test_disable(self):
        # Given a view.
        self.assertIsNotNone(self.view.parent)
        # When disabling or enabling
        self.view.disable = True
        await self.pump_events()
        self.view.disable = False
        await self.pump_events()
        # Then no error occur
