# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty
from kivymd.uix.boxlayout import MDBoxLayout

from minarca_client.core import BackupInstance
from minarca_client.locale import _  # noqa

logger = logging.getLogger(__name__)

Builder.load_string(
    '''
<BackupRestore>:
    orientation: "horizontal"
    md_bg_color: self.theme_cls.backgroundColor

    SidePanel:
        is_remote: root.is_remote
        restore: True
        text: _("Choose between restoring all files in place or selecting specific files for restoration.")

    MDScrollView:
        size_hint: 1, 1
        pos_hint: {'right': 1}
        bar_width: 10

        MDBoxLayout:
            orientation: "vertical"
            padding: "50dp"
            spacing: "15dp"
            adaptive_height: True

            CLabel:
                text: _("Restore Options")
                font_style: "Title"
                role: "small"
                text_color: self.theme_cls.primaryColor

            MDBoxLayout:
                cols: 2
                spacing: "20dp"
                adaptive_height: True

                CCard:
                    orientation: 'vertical'
                    spacing: "10dp"
                    adaptive_height: True

                    MDIcon:
                        icon: "target"
                        theme_font_size: "Custom"
                        font_size: "60dp"
                        size_hint_x: 1
                        padding: 0, "20dp", 0, "20dp"

                    CLabel:
                        text: _("Custom restore")
                        font_style: "Title"
                        text_color: self.theme_cls.primaryColor
                        halign: "center"

                    MDDivider:

                    CLabel:
                        text: _("Select file(s) to restore")
                        halign: "center"

                    MDDivider:

                    CLabel:
                        text: _("Select destination")
                        halign: "center"

                    MDDivider:

                    CLabel:
                        text: _("Ideal for quick recovery")
                        halign: "center"

                    MDDivider:

                    CButton:
                        text: _("Custom restore")
                        pos_hint: {"center_x": .5}
                        on_release: root.custom_restore()

                CCard:
                    orientation: 'vertical'
                    spacing: "10dp"
                    adaptive_height: True

                    MDIcon:
                        icon: "backup-restore"
                        theme_font_size: "Custom"
                        font_size: "60dp"
                        size_hint_x: 1
                        padding: 0, "20dp", 0, "20dp"

                    CLabel:
                        text: _("Full restore")
                        font_style: "Title"
                        text_color: self.theme_cls.primaryColor
                        halign: "center"

                    MDDivider:

                    CLabel:
                        text: _("Restore all files")
                        halign: "center"

                    MDDivider:

                    CLabel:
                        text: _("Replace existing files")
                        halign: "center"

                    MDDivider:

                    CLabel:
                        text: _("Ideal for hardware failure")
                        halign: "center"

                    MDDivider:

                    CButton:
                        text: _("Full restore")
                        pos_hint: {"center_x": .5}
                        on_release: root.full_restore()

            CButton:
                text: _('Back')
                on_release: root.cancel()
                theme_bg_color: "Custom"
                md_bg_color: self.theme_cls.inverseSurfaceColor

'''
)


class BackupRestore(MDBoxLayout):
    instance = None
    is_remote = BooleanProperty()

    def __init__(self, backup=None, instance=None):
        assert backup
        assert instance and isinstance(instance, BackupInstance)
        # Initialise the state.
        self.instance = instance
        self.is_remote = self.instance.is_remote()
        # Create the view
        super().__init__()

    def full_restore(self):
        App.get_running_app().set_active_view('BackupRestoreDate', instance=self.instance, restore_type='full')

    def custom_restore(self):
        App.get_running_app().set_active_view('BackupRestoreDate', instance=self.instance, restore_type='custom')

    def cancel(self):
        # Go back to dashboard
        App.get_running_app().set_active_view('DashboardView')
