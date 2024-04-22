# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.textinput import TextInput
from kivymd.uix.boxlayout import MDBoxLayout

from minarca_client.core import BackupInstance
from minarca_client.core.compat import open_file_with_default_app, tail, watch_file
from minarca_client.dialogs import error_dialog, question_dialog
from minarca_client.locale import _
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)

MAX_LINES = 1000

Builder.load_string(
    '''
<LogLine>:
    padding: 0
    multiline: False
    readonly: True
    theme_font_name: "Custom"
    font_name: "monospace"
    background_color: app.theme_cls.surfaceColor
    text_color: app.theme_cls.onSurfaceColor
    background_normal: ""
    background_active: ""
    background_disabled_normal: ""

<BackupLogs>:
    orientation: "horizontal"
    md_bg_color: self.theme_cls.backgroundColor

    SidePanel:
        is_remote: root.is_remote
        create: False
        text: _("Get detailed information about you last backup or restore operation.")

    MDBoxLayout:
        orientation: "vertical"
        padding: "50dp"
        spacing: "15dp"

        MDBoxLayout:
            orientation: "horizontal"
            spacing: "15dp"
            adaptive_height: True


            CLabel:
                text: root.title_text
                font_style: "Title"
                role: "small"
                text_color: self.theme_cls.primaryColor
                adaptive_size: True

            Widget:

            CLabel:
                text: root.last_status_text
                halign: "right"
                adaptive_size: True

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

            Widget:

            MDIconButton:
                icon: "stop"
                on_release: root.stop()
                theme_icon_color: "Custom"
                icon_color: app.theme_cls.onSurfaceColor

        CLabel:
            text: root.error_message
            text_color: self.theme_cls.onWarningColor
            md_bg_color: self.theme_cls.warningColor
            padding: ("15dp", "12dp")
            display: root.error_message

        CCard:
            padding: "1dp"

            RecycleView:
                id: logview
                viewclass: "LogLine"
                data: root.lines

                RecycleBoxLayout:
                    padding: "0dp"
                    default_size: None, "22dp"
                    default_size_hint: 1, None
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height

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
    instance = None
    is_remote = BooleanProperty()
    status = ObjectProperty()
    lines = ListProperty()
    _status_task = None
    _readlogs_task = None
    _stop_task = None

    def __init__(self, backup=None, instance=None):
        assert backup
        assert instance and isinstance(instance, BackupInstance)
        # Initialise the state.
        self.instance = instance
        self.is_remote = self.instance.is_remote()
        self.status = self.instance.status
        # Create the view
        super().__init__()
        # Register task to update status.
        self._status_task = asyncio.create_task(self._watch_status(instance))
        # Load log file
        self._readlogs_task = asyncio.create_task(self._readlogs(instance))

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._readlogs_task:
            self._readlogs_task.cancel()
        if self._status_task:
            self._status_task.cancel()
        if self._stop_task:
            self._stop_task.cancel()

    async def _watch_status(self, instance):
        # Asynchronously watch the status files for changes.
        """
        Special implementation of awatch forcing update after 5 seconds of inativity when running.
        """
        try:
            last_action = self.status.action
            async for unused in watch_file(self.status, timeout=self.status.RUNNING_DELAY):
                self.status.reload()
                self.property('status').dispatch(self)
                # When action changes, reload the log file.
                if last_action != self.status.action:
                    last_action = self.status.action
                    if self._readlogs_task:
                        self._readlogs_task.cancel()
                    self._readlogs_task = asyncio.create_task(self._readlogs(instance))
        except Exception:
            logger.exception('problem occured while watching status')

    async def _readlogs(self, instance):
        try:
            # Get the backup or restore log file.
            fn = self.filename
            if not fn:
                return
            # Clear log view
            self.lines = []
            # Open file content.
            async for line in tail(fn, num_lines=MAX_LINES):
                self.lines.append({"text": line.decode('utf-8', errors='replace')})
                if len(self.lines) >= 24 and self.is_running:
                    # Move cursor to the end if running.
                    self.scroll_down()
                # Limit number of lines to 1000
                if len(self.lines) >= 1000:
                    self.lines.pop(0)
        except Exception:
            logger.exception('problem occured while reading backup logs')

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

    @alias_property(bind=['status'])
    def last_status_text(self):
        """Return the last backup description."""
        is_running = self.is_running
        if self.status and self.status.lastdate:
            value = self.status.lastdate.strftime("%a, %d %b %Y %H:%M")
        else:
            return _('No backup yet')
        if not is_running:
            action = self.status.action
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

    @alias_property(bind=['status'])
    def filename(self):
        action = self.status.action
        if action == 'backup':
            return self.instance.backup_log_file
        elif action == 'restore':
            return self.instance.restore_log_file

    def open_log_file(self):
        if self.filename:
            open_file_with_default_app(self.filename)

    def scroll_down(self):
        # Jump directly to the end of the log file.
        self.ids.logview.scroll_y = 0

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
        App.get_running_app().set_active_view('DashboardView')
