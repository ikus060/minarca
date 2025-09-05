# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout

from minarca_client.core import BackupInstance
from minarca_client.dialogs import warning_dialog
from minarca_client.locale import _
from minarca_client.ui.spinner_overlay import SpinnerOverlay  # noqa

logger = logging.getLogger(__name__)

Builder.load_string(
    '''
<BackupAdvanceSettings>:
    orientation: "horizontal"
    md_bg_color: self.theme_cls.backgroundColor

    SidePanel:
        is_remote: root.is_remote
        create: False
        text: _("Configure your advanced backup settings to fine-tune your preferences.")

    MDRelativeLayout:

        MDScrollView:
            size_hint: 1, 1
            pos_hint: {'right': 1}

            MDBoxLayout:
                orientation: "vertical"
                padding: "50dp"
                spacing: "25dp"
                adaptive_height: True

                CLabel:
                    text: _('Script hooks')
                    font_style: "Title"
                    role: "small"
                    text_color: self.theme_cls.primaryColor

                CLabel:
                    text: _("Set up custom scripts to run before or after backups by defining the command line to be executed.")

                CTextField:
                    name: _("Pre-backup command")
                    text: root.pre_hook_command
                    on_text: root.pre_hook_command = self.text

                CTextField:
                    name: _("Post-backup command")
                    text: root.post_hook_command
                    on_text: root.post_hook_command = self.text

                CCheckbox:
                    text: _("Continue the backup if one of the command fails")
                    active: root.ignore_hook_errors
                    on_active: root.ignore_hook_errors = self.active

                MDBoxLayout:
                    orientation: "horizontal"
                    spacing: "10dp"
                    adaptive_height: True
                    padding: (0, "30dp", 0 , 0)

                    CButton:
                        id: btn_cancel
                        text: _('Cancel')
                        on_release: root.cancel()
                        disabled: root.working
                        theme_bg_color: "Custom"
                        md_bg_color: self.theme_cls.inverseSurfaceColor

                    CButton:
                        id: btn_save
                        text: _('Save')
                        on_release: root.save()
                        disabled: root.working

        SpinnerOverlay:
            text: root.working
            display: bool(root.working)

'''
)


class BackupAdvanceSettings(MDBoxLayout):
    is_remote = BooleanProperty(True)
    pre_hook_command = StringProperty()
    post_hook_command = StringProperty()
    ignore_hook_errors = BooleanProperty(False)
    working = StringProperty()

    def __init__(self, backup=None, instance=None, create=False):
        """Edit or create backup configuration for the given instance"""
        assert backup
        assert instance and isinstance(instance, BackupInstance)
        # Initialise the state.
        self.backup = backup
        self.instance = instance
        self.is_remote = instance.is_remote()

        # Load settings from local values
        settings = self.instance.settings
        self.pre_hook_command = settings.pre_hook_command or ""
        self.post_hook_command = settings.post_hook_command or ""
        self.ignore_hook_errors = settings.ignore_hook_errors

        # Create the view
        super().__init__()

    def cancel(self):
        # Go to dashboard view.
        App.get_running_app().set_active_view('dashboard.DashboardView')

    def save(self):
        if self.working:
            # Operation should not be accessible if already working.
            return
        self.working = _('Please wait. Saving settings...')
        self._save_task = asyncio.create_task(self._save())

    async def _save(self):
        try:
            # Save settings
            settings = self.instance.settings
            settings.pre_hook_command = self.pre_hook_command
            settings.post_hook_command = self.post_hook_command
            settings.ignore_hook_errors = self.ignore_hook_errors
            settings.save()
            # Redirect user to dashboard.
            App.get_running_app().set_active_view('dashboard.DashboardView')
        except Exception as e:
            logger.exception('problem encountered while saving advance backup settings')
            await warning_dialog(
                parent=self,
                title=_('Cannot save advance settings'),
                message=_(
                    'An unknown problem encountered while trying to save the advance backup settings. If the problem persist contact your administrator.'
                ),
                detail=str(e),
            )
        finally:
            self.working = ''
