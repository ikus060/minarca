# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout

from minarca_client.core import BackupInstance
from minarca_client.locale import _
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)

Builder.load_string(
    '''
<BackupLogs>:
    orientation: "horizontal"
    md_bg_color: app.white

    SidePanel:
        is_remote: True
        create: False
        text: _("Get detailed information about you last backup execution.")

    MDBoxLayout:
        orientation: "vertical"
        padding: "50dp"
        spacing: "15dp"

        MDBoxLayout:
            orientation: "horizontal"
            adaptive_height: True

            CLabel:
                text: _("Backup logs")
                font_style: "Title"
                role: "small"
                text_color: app.primary

            CLabel:
                text: root.last_status_text
                halign: "right"

        CLabel:
            text: root.error_message
            text_color: app.white
            md_bg_color: app.warning
            padding: ("15dp", "12dp")
            display: root.error_message

        CCard:
            padding: "1dp"

            TextInput:
                id: logview
                font_name: "monospace"
                readonly: True
                multiline: True
                do_wrap: False
                text: _("Loading...")
                background_color: app.theme_cls.surfaceColor
                text_color: app.theme_cls.onSurfaceColor
                background_normal: ""
                background_active: ""
                adaptive_height: True

        CButton:
            text: _('Back')
            on_release: root.cancel()
            theme_bg_color: "Custom"
            md_bg_color: app.dark
'''
)


class BackupLogs(MDBoxLayout):
    instance = None
    status = ObjectProperty()

    def __init__(self, master=None, backup=None, instance=None):
        assert backup
        assert instance and isinstance(instance, BackupInstance)
        # Initialise the state.
        self.instance = instance
        self.status = self.instance.status
        # Create the view
        super().__init__(master)
        # Register a task to read log file.
        self._readlogs_task = asyncio.get_event_loop().create_task(self._readlogs(instance))

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._readlogs_task:
            self._readlogs_task.cancel()

    async def _readlogs(self, instance):
        try:
            # Get the backup or restore log file.
            logview = self.ids['logview']
            action = self.instance.status.action
            if action == 'backup':
                fn = self.instance.backup_log_file
            elif action == 'restore':
                fn = self.instance.restore_log_file
            else:
                logview.text = ""
                return
            # Open file content. Limit to 1MiB
            try:
                with open(fn, 'r') as f:
                    logview.text = f.read(1024 * 1024)
            except IOError:
                pass  # Do nothing if the file cannot be open.
        except Exception:
            logger.exception('problem occured while reading backup logs')

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

    @alias_property(bind=['status'])
    def last_status_success(self):
        """Return corresponding icon depending of the last backup status."""
        return self.status and self.status.current_status in ['SUCCESS', 'RUNNING']

    @alias_property(bind=['status'])
    def error_message(self):
        if self.status is None:
            return ""
        return self.status.details or ""

    def cancel(self):
        # Go back to dashboard
        App.get_running_app().set_active_view('DashboardView')
