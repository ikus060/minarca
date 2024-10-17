# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout

from minarca_client.core import BackupInstance
from minarca_client.core.compat import open_file_with_default_app
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

    MDFloatLayout:

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
                    text: _("Set up custom scripts to run before or after backups by placing them in designated folders.")

                CCheckbox:
                    text: _("Run script(s) before backup")
                    active: root.pre_enabled
                    on_active: root.pre_enabled = not root.pre_enabled

                CCheckbox:
                    text: _("Continue the backup if one of the script execution fails")
                    active: root.pre_ignore_error
                    on_active: root.pre_ignore_error = not root.pre_ignore_error
                    disabled: not root.pre_enabled

                CCheckbox:
                    text: _("Run script(s) after backup")
                    active: root.post_enabled
                    on_active: root.post_enabled = not root.post_enabled

                CCheckbox:
                    text: _("Execute script(s) after backup, even if backup fails")
                    active: root.post_ignore_error
                    on_active: root.post_ignore_error = not root.post_ignore_error
                    disabled: not root.post_enabled

                CButton:
                    text: _('Open hooks folders')
                    role: "small"
                    on_release: root.open_hooks_dir()
                    disabled: not root.post_enabled and not root.pre_enabled

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

# TODO
# On Window,s will support "vbs", "cmd", "ps1", "bat" ?
# On Linux/MacOS we support anything ? start with proper shebang


class BackupAdvanceSettings(MDBoxLayout):
    is_remote = BooleanProperty(True)
    pre_enabled = BooleanProperty(False)
    pre_ignore_error = BooleanProperty(False)
    post_enabled = BooleanProperty(False)
    post_ignore_error = BooleanProperty(False)
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
        flags = settings.flags
        if flags is not None:
            self.pre_enabled = flags & settings.PRE_ENABLED
            self.pre_ignore_error = flags & settings.PRE_IGNORE_ERROR
            self.post_enabled = flags & settings.POST_ENABLED
            self.post_ignore_error = flags & settings.POST_IGNORE_ERROR

        # Create the view
        super().__init__()

    def cancel(self):
        # Go to dashboard view.
        App.get_running_app().set_active_view('DashboardView')

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
            flags = settings.flags
            for value, flag in [
                (self.pre_enabled, settings.PRE_ENABLED),
                (self.pre_ignore_error, settings.PRE_IGNORE_ERROR),
                (self.post_enabled, settings.POST_ENABLED),
                (self.post_ignore_error, settings.POST_IGNORE_ERROR),
            ]:
                if value:
                    flags |= flag
                else:
                    flags &= ~flag
            settings.flags = flags
            settings.save()
            # Redirect user to dashboard.
            App.get_running_app().set_active_view('DashboardView')
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

    def open_hooks_dir(self):
        if self.working:
            # Operation should not be accessible if already working.
            return
        self.working = _('Please wait. Opening post-hooks folder...')
        self._save_task = asyncio.create_task(self._open_hook_dir())

    async def _open_hook_dir(self):
        """Used to create and open the hook folder."""
        try:
            self.instance.create_hooks_dir()
            if self.pre_enabled:
                open_file_with_default_app(self.instance.pre_hooks_dir)
            if self.post_enabled:
                open_file_with_default_app(self.instance.post_hooks_dir)
        except FileExistsError as e:
            logger.exception('file already exists')
            await warning_dialog(
                parent=self,
                title=_('Cannot create hook folder'),
                message=_(
                    "The location `%s` already exists, but it's not a folder. Please delete this file and try again."
                )
                % e[0],
            )
        except Exception as e:
            logger.exception('problem encountered when creating a hook folders')
            await warning_dialog(
                parent=self,
                title=_('Cannot create hook folders'),
                message=_(
                    'An unknown problem has been encountered when creating hook folders. If the problem persists, please contact your administrator.'
                ),
                detail=str(e),
            )
        finally:
            self.working = ''
