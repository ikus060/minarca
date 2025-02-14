# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty

from minarca_client.ui.theme import CScrollView

Builder.load_string(
    '''
<BackupCreate>:
    orientation: 'vertical'
    theme_bg_color: "Custom"
    md_bg_color: app.theme_cls.surfaceContainerColor
    adaptive_height: True

    MDBoxLayout:
        padding: "30dp"
        spacing: "30dp"
        orientation: 'vertical'
        adaptive_height: True

        MDBoxLayout:
            orientation: 'horizontal'
            adaptive_height: True

            CLabel:
                text: _("Create a backup")
                role: "large"
                font_style: "Title"
                halign: "left" if root.backup_exists else "center"

            CButton:
                text: _('Back')
                theme_bg_color: "Custom"
                md_bg_color: self.theme_cls.inverseSurfaceColor
                on_press: root.cancel()
                display: root.backup_exists

        MDBoxLayout:
            cols: 2
            spacing: "20dp"
            adaptive_height: True

            Widget:
                adaptive_height: True

            CCard:
                orientation: 'vertical'
                spacing: "10dp"
                size_hint_x: None
                width: "320dp"
                adaptive_height: True

                Image:
                    source: "remote-backup-128.png"
                    fit_mode: "contain"
                    height: "128dp"
                    size_hint_y: None

                CLabel:
                    text: _("Online backup")
                    font_style: "Title"
                    text_color: self.theme_cls.primaryColor
                    halign: "center"

                MDDivider:

                CLabel:
                    text: _("Dedicated centralized server")
                    halign: "center"

                MDDivider:

                CLabel:
                    text: _("Accessible anywhere")
                    halign: "center"

                MDDivider:

                CLabel:
                    text: _("Remote backup")
                    halign: "center"

                MDDivider:

                CButton:
                    text: _("Setup")
                    pos_hint: {"center_x": .5}
                    on_release: root._create_remote()

            CCard:
                orientation: 'vertical'
                spacing: "10dp"
                size_hint_x : None
                width: "320dp"
                adaptive_height: True

                Image:
                    source: "local-backup-128.png"
                    fit_mode: "contain"
                    height: "128dp"
                    size_hint_y: None

                CLabel:
                    text: _("Local backup")
                    font_style: "Title"
                    text_color: self.theme_cls.primaryColor
                    halign: "center"

                MDDivider:

                CLabel:
                    text: _("External disk or network share")
                    halign: "center"

                MDDivider:

                CLabel:
                    text: _("Offline accessibility")
                    halign: "center"

                MDDivider:

                CLabel:
                    text: _("Standalone backup")
                    halign: "center"

                MDDivider:

                CButton:
                    text: _("Setup")
                    pos_hint: {"center_x": .5}
                    on_release: root._create_local()

            Widget:
                adaptive_height: True

'''
)


class BackupCreate(CScrollView):
    backup_exists = BooleanProperty(False)

    def __init__(self, backup=None):
        super().__init__()
        assert backup is not None
        self.backup_exists = len(backup) > 0

    def _create_remote(self):
        App.get_running_app().set_active_view('backup_connection_remote.BackupConnectionRemote', create=True)

    def _create_local(self):
        App.get_running_app().set_active_view('backup_connection_local.BackupConnectionLocal', create=True)

    def cancel(self):
        App.get_running_app().set_active_view('dashboard.DashboardView')
