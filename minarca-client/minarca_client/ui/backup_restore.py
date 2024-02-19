# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout

from minarca_client.core import BackupInstance
from minarca_client.locale import _
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)

Builder.load_string(
    '''
<BackupRestore>:
    orientation: "horizontal"
    md_bg_color: app.white

    SidePanel:
        is_remote: True
        create: False
        text: _("Choose between restoring all files in place or selecting specific files for restoration.")

    MDFloatLayout:

        MDScrollView:
            size_hint: 1, 1
            pos_hint: {'right': 1}

            MDBoxLayout:
                orientation: "vertical"
                padding: "50dp"
                spacing: "15dp"
                adaptive_height: True

                MDBoxLayout:
                    orientation: "horizontal"
                    adaptive_height: True

                    CLabel:
                        text: _("Restore Options")
                        font_style: "Title"
                        role: "small"
                        text_color: app.primary

                    CLabel:
                        text: root.last_status_text
                        halign: "right"

                MDBoxLayout:
                    cols: 2
                    spacing: "20dp"
                    adaptive_height: True

                    CCard:
                        orientation: 'vertical'
                        spacing: "10dp"
                        adaptive_height: True

                        Image:
                            source: "remote-backup-128.png"
                            height: "128dp"
                            size_hint_y: None

                        CLabel:
                            text: _("All files")
                            font_style: "Title"
                            text_color: app.primary
                            halign: "center"

                        MDDivider:

                        CLabel:
                            text: _("Full restore")
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
                            text: _("Restore")
                            pos_hint: {"center_x": .5}
                            on_release: root.full_restore()

                    CCard:
                        orientation: 'vertical'
                        spacing: "10dp"
                        adaptive_height: True

                        Image:
                            source: "local-backup-128.png"
                            height: "128dp"
                            size_hint_y: None

                        CLabel:
                            text: _("Specific files")
                            font_style: "Title"
                            text_color: app.primary
                            halign: "center"

                        MDDivider:

                        CLabel:
                            text: _("Select file to restore")
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
                            text: _("Restore")
                            pos_hint: {"center_x": .5}
                            on_release: root.partial_restore()

                CButton:
                    text: _('Back')
                    on_release: root.cancel()
                    theme_bg_color: "Custom"
                    md_bg_color: app.dark

        CBoxLayout:
            orientation: "vertical"
            size_hint: 1, 1
            md_bg_color: [1, 1, 1, 0.5]
            spacing: "30dp"
            pos_hint: {'center_x': .5, 'center_y': .5}
            display: root.working

            Widget:
                size_hint_y: 0.5

            CSpinner:

            CLabel:
                text: _("Please wait")
                halign: "center"
                pos_hint: {'center_x': .5, 'center_y': .5}

            Widget:
'''
)


class BackupRestore(MDBoxLayout):
    instance = None
    status = ObjectProperty()
    working = BooleanProperty(False)

    def __init__(self, master=None, backup=None, instance=None):
        assert backup
        assert instance and isinstance(instance, BackupInstance)
        # Initialise the state.
        self.instance = instance
        self.status = self.instance.status
        # Create the view
        super().__init__(master)

    @alias_property(bind=['status'])
    def last_status_text(self):
        """Return the last backup description."""
        if self.status and self.status.lastdate:
            value = self.status.lastdate.strftime("%a, %d %b %Y %H:%M")
        else:
            return _('No backup yet')
        action = self.instance.status.action
        if action == 'backup':
            return _('Last backup: %s') % value
        elif action == 'restore':
            return _('Last restore: %s') % value
        return ""

    def full_restore(self):
        pass

    def partial_restore(self):
        pass

    def cancel(self):
        # Go back to dashboard
        App.get_running_app().set_active_view('DashboardView')
