from minarca_client.core.instance import BackupInstance
from minarca_client.ui.app import BackupCreate, DashboardView
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

    async def test_disable(self):
        # Given a view.
        self.assertIsNotNone(self.view.parent)
        # When disabling or enabling
        self.view.disable = True
        await self.pump_events()
        self.view.disable = False
        await self.pump_events()
        # Then no error occur
