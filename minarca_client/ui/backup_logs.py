# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging

import aiofiles
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.textinput import TextInput
from kivymd.uix.boxlayout import MDBoxLayout

from minarca_client.core.compat import open_file_with_default_app, watch_file
from minarca_client.dialogs import error_dialog, question_dialog
from minarca_client.locale import _
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 1024 * 10  # Max size to process (e.g., 10 KB)
UPDATE_INTERVAL = 1  # Update interval in seconds

Builder.load_string(
    '''
<BackupLogs>:
    orientation: "horizontal"
    md_bg_color: self.theme_cls.backgroundColor

    # Bind instance view model
    status: root.instance.status if root.instance else None
    is_remote: self.instance.is_remote() if root.instance else True

    SidePanel:
        is_remote: root.is_remote
        create: False
        text: _("Get detailed information about your last backup or restore operation.")

    MDBoxLayout:
        orientation: "vertical"
        padding: "50dp"
        spacing: "15dp"

        CBoxLayout:
            orientation: 'horizontal'
            padding: ("15dp", "7dp")
            spacing: "10dp"
            theme_bg_color: "Custom"
            md_bg_color: app.theme_cls.warningContainerColor
            display: root.is_running
            adaptive_height: True
            canvas.after:
                Color:
                    rgba: app.theme_cls.warningColor
                Line:
                    rectangle: [self.x, self.y, self.width, self.height]
                    width: 1

            CSpinner:
                color: app.theme_cls.warningColor
                size_hint: None, None
                size: "16dp", "16dp"
                pos_hint: {'center_y': .5}

            CLabel:
                text: root.is_running_text
                pos_hint: {'center_y': .5}
                adaptive_size: True

            Widget:

            MDIconButton:
                icon: "stop"
                on_release: root.stop()
                theme_icon_color: "Custom"
                icon_color: app.theme_cls.onSurfaceColor

        MDTabsSecondary:
            id: tabs
            indicator_height: "3dp"

            MDTabsItemSecondary:
                id: log_tab
                on_release: root.tab = 'backup'

                MDTabsItemIcon:
                    icon: "content-copy"

                MDTabsItemText:
                    text: _('Backup logs')

            MDTabsItemSecondary:
                id: exclude_tab
                on_release: root.tab = 'restore'

                MDTabsItemIcon:
                    icon: "restore"

                MDTabsItemText:
                    text: _('Restore logs')

            MDDivider:

        CLabel:
            text: root.error_message
            text_color: self.theme_cls.onWarningColor
            md_bg_color: self.theme_cls.warningContainerColor
            padding: ("15dp", "12dp")
            display: root.error_message

        CScrollView:
            id: scrollv
            canvas.after:
                Color:
                    rgba: app.theme_cls.onSurfaceColor
                Line:
                    rectangle: [self.x, self.y, self.width, self.height]
                    width: 1

            TextInput:
                id: logview
                size_hint: 1, None
                height: max(self.minimum_height, scrollv.height)
                font_name: "monospace"
                readonly: True
                # Change style of TextInput.
                background_color: app.theme_cls.surfaceColor
                text_color: app.theme_cls.onSurfaceColor
                background_normal: ""
                background_active: ""

        MDBoxLayout:
            orientation: "horizontal"
            adaptive_height: True

            CButton:
                id: btn_cancel
                text: _('Back')
                on_release: root.cancel()
                theme_bg_color: "Custom"
                md_bg_color: self.theme_cls.inverseSurfaceColor

            Widget:

            CButton:
                style: "text"
                text: _("Open file in text editor...")
                on_release: root.open_log_file()
                disabled: not root.filename

            CButton:
                style: "text"
                text: _("Scroll to bottom")
                on_release: root.scroll_down()
'''
)


class LogLine(TextInput, RecycleDataViewBehavior):
    def refresh_view_attrs(self, rv, index, data):
        ret = super().refresh_view_attrs(rv, index, data)
        # When reusing widgets, reinitialize the scroll.
        self.scroll_x = 0
        self.cursor = (0, 0)
        self.select_text(0, 0)
        return ret


class BackupLogs(MDBoxLayout):
    instance = ObjectProperty(None, rebind=True)
    status = ObjectProperty(None, allownone=True, rebind=True)
    is_remote = BooleanProperty()
    tab = StringProperty()
    _readlogs_task = None
    _stop_task = None

    def __init__(self, backup=None, instance=None, tab='backup'):
        assert backup
        assert instance
        # Initialise the state.
        self.instance = instance
        self.tab = tab
        # Create the view
        super().__init__()
        # Make the default tabs active
        self.ids['log_tab'].on_release()
        # Load log file
        self._readlogs_task = asyncio.create_task(self._readlogs())

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._readlogs_task:
            self._readlogs_task.cancel()
        if self._stop_task:
            self._stop_task.cancel()

    async def _readlogs(self):
        if not self.filename:
            return
        try:
            # Due to Kivy limitation of TextInput updating all the lines at once. We need to
            # Reload the logs less often and limit the number of lines to keep the interface responsible.
            logview = self.ids.logview
            logview.text = await self.read_file_tail(self.filename)
            logview.parent.scroll_y = 0
            async for unused in watch_file(self.filename, poll_delay=UPDATE_INTERVAL):
                logview.text = await self.read_file_tail(self.filename)
        except Exception:
            logger.exception('problem occured while reading backup logs')

    async def read_file_tail(self, file_path):
        """
        Read the last part of the file if its size exceeds MAX_FILE_SIZE.
        """
        try:
            async with aiofiles.open(file_path, "rb") as f:
                await f.seek(0, 2)  # Move to the end of the file
                file_size = await f.tell()

                if file_size > MAX_FILE_SIZE:
                    # Read only the last MAX_FILE_SIZE bytes
                    await f.seek(-MAX_FILE_SIZE, 2)
                    content = '<Log truncated>\n...'
                    data = await f.read()
                    # Try to cut the data at line ending.
                    try:
                        idx = data.index(b'\n')
                        data = data[idx:]
                    except ValueError:
                        pass
                    content += data.decode("utf-8", errors="replace")
                else:
                    # Read the entire file
                    await f.seek(0)
                    data = await f.read()
                    content = data.decode("utf-8", errors="replace")
            return content
        except FileNotFoundError:
            return _('No log')

    @alias_property(bind=['status'])
    def title_text(self):
        action = self.status.action
        if action == 'restore':
            return _('Restore logs')
        return _('Backup logs')

    @alias_property(bind=['status'])
    def is_running_text(self):
        if self.status:
            action = self.status.action
            if action == 'backup':
                return _('Backup in progress for %s...') % self.instance.settings.repositoryname
            elif action == 'restore':
                return _('Data restoration in progress for %s...') % self.instance.settings.repositoryname
        return ""

    @alias_property(bind=['status'])
    def is_running(self):
        return self.status and self.status.current_status in ['RUNNING', 'STALE']

    @alias_property(bind=['status', 'tab'])
    def error_message(self):
        if self.status is None:
            return ""
        if self.status.details:
            action = self.status.action
            if action == 'backup' and self.tab == 'backup':
                return _('The last backup ended with the following error: %s') % self.status.details
            elif action == 'restore' and self.tab == 'restore':
                return _('The last restoration ended with the following error: %s') % self.status.details
        return ""

    @alias_property(bind=['tab'])
    def filename(self):
        if self.tab == 'backup':
            return self.instance.backup_log_file
        elif self.tab == 'restore':
            return self.instance.restore_log_file

    def on_filename(self, *args, **kwargs):
        # Reload log view when filename get updated.
        if self._readlogs_task:
            self._readlogs_task.cancel()
        self.ids.logview.text = ""
        self._readlogs_task = asyncio.create_task(self._readlogs())

    def open_log_file(self):
        if self.filename:
            open_file_with_default_app(self.filename)

    def scroll_down(self):
        # Jump directly to the end of the log file.
        self.ids.logview.parent.scroll_y = 0

    def stop(self):
        async def _stop():
            ret = await question_dialog(
                parent=self,
                title=_('Confirmation Required'),
                message=_('Are you sure you want to stop the ongoing backup/restore process?'),
                detail=_(
                    'Your data may be incomplete or corrupted if the operation is terminated prematurely. Please confirm your decision before proceeding.'
                ),
            )
            if not ret:
                # Operation cancel by user
                return
            try:
                self.instance.stop()
            except Exception as e:
                logger.exception('fail to stop')
                await error_dialog(
                    title=_("Stop process"),
                    message=_("A problem occurred when trying to stop the process."),
                    detail=str(e),
                )

        self._stop_task = asyncio.create_task(_stop())

    def cancel(self):
        # Go back to dashboard
        App.get_running_app().set_active_view('dashboard.DashboardView')
