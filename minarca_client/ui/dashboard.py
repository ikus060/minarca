# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import itertools
import logging

from kivy.app import App
from kivy.lang import Builder
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
                padding: "30dp", "30dp", "30dp", 0

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
                padding: "30dp"
                cols: 2
                adaptive_height: True
'''
)


class DashboardView(MDBoxLayout):

    def __init__(self, backup=None):
        assert backup is not None
        super().__init__()
        self.refresh_cards(backup, backup.instances)
        backup.bind(instances=self.refresh_cards)

    def refresh_cards(self, widget, instances):
        parent = self.ids.card_list
        children = parent.children
        for instance, backup_card in itertools.zip_longest(instances.values(), children):
            if backup_card is None:
                backup_card = BackupCard()
                parent.add_widget(backup_card)
            if instance is None:
                parent.remove_widget(backup_card)
            else:
                backup_card.instance = instance

    def create_backup(self):
        App.get_running_app().set_active_view('backup_create.BackupCreate')
