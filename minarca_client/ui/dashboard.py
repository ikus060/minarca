# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import itertools
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ListProperty
from kivymd.uix.boxlayout import MDBoxLayout

from .backup_card import BackupCard  # noqa

logger = logging.getLogger(__name__)

Builder.load_string(
    '''
<DashboardView>:
    orientation: 'vertical'
    md_bg_color: self.theme_cls.surfaceContainerColor

    CScrollView:

        MDBoxLayout:
            orientation: 'vertical'
            adaptive_height: True

            MDBoxLayout:
                orientation: 'horizontal'
                adaptive_height: True
                padding: "40dp", "40dp", "40dp", 0

                CLabel:
                    text: _('Dashboard')
                    role: "large"
                    font_style: "Title"

                CButton:
                    text: _('Setup backup')
                    on_release: root.create_backup()

            MDGridLayout:
                id: card_list
                orientation: 'lr-tb'
                -spacing: "20dp" if len(self.children)>1 else 0
                padding: "40dp"
                cols: 2
                adaptive_height: True
'''
)


class DashboardView(MDBoxLayout):
    instances = ListProperty()

    _task = None

    def __init__(self, backup=None):
        assert backup is not None
        super().__init__()
        # Initialize the instance list
        self.instances = list(backup)
        # Keep the view up-to-date by refreshing the instances
        self._task = asyncio.create_task(self._watch_instances(backup))

    def on_parent(self, instance, value):
        if value is None and self._task:
            self._task.cancel()

    def on_instances(self, widget, value):
        children = self.ids.card_list.children
        for instance, backup_card in itertools.zip_longest(value, children):
            if backup_card is None:
                backup_card = BackupCard()
                self.ids.card_list.add_widget(backup_card)
            backup_card.instance = instance
            if instance is None:
                backup_card.parent.remove_widget(backup_card)

    async def _watch_instances(self, backup):
        """
        Watch changes to instances.
        """
        try:
            async for unused in backup.awatch():
                self.instances = list(backup)
        except Exception:
            logger.exception('problem occur while watching backup instances')

    def create_backup(self):
        App.get_running_app().set_active_view('BackupCreate')
