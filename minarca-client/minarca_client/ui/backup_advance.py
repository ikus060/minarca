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
from minarca_client.dialogs import question_dialog, warning_dialog
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
        text: _("Configure your advance backup settings.")

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
                    text: _('Advance backup settings')
                    font_style: "Title"
                    role: "small"
                    text_color: self.theme_cls.primaryColor

                CCheckbox:
                    text: _("Execute script(s) before and after backup")
                    active: root.execute_scripts
                    on_active: root.execute_scripts = not root.execute_scripts

                CCheckbox:
                    text: _("Continue the backup if one of the script execution fails")
                    active: root.continue_on_error
                    on_active: root.continue_on_error = not root.continue_on_error
                    disabled: not root.execute_scripts

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

# TODO Add a little info about script permissions and list of supported script.
# Required mode 644
# On Window,s will support "vbs", "cmd", "ps1", "bat" ?
# On Linux/MacOS we support anything ? start with proper shebang

# TODO Add a button to open script folder location.
# If this location doesn't exists. prompt user to create the folder. Similar to Zim.

class BackupAdvanceSettings(MDBoxLayout):
    is_remote = BooleanProperty(True)
    execute_scripts = BooleanProperty(False)
    continue_on_error = BooleanProperty(False)
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
        if settings.hook is not None:
            self.execute_scripts = settings.hook & settings.HOOK_ENABLED
            self.continue_on_error = settings.hook & settings.HOOK_CONTINUE_ON_ERROR

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
            hook = 0
            if self.execute_script:
                hook |= settings.HOOK_ENABLED
            if self.continue_on_error:
                hook |= settings.HOOK_CONTINUE_ON_ERROR
            settings.save()
            # Redirect user to dashboard.
            App.get_running_app().set_active_view('DashboardView')
        except Exception as e:
            logger.exception('problem occured while saving advance backup settings')
            await warning_dialog(
                parent=self,
                title=_('Cannot save advance settings'),
                message=_(
                    'An unknown problem occured while trying to save the advance backup settings. If the problem persist contact your administrator.'
                ),
                detail=str(e),
            )
        finally:
            self.working = ''
