# Copyleft (C) 2023 IKUS Software. All lefts reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging
import tkinter.messagebox

from minarca_client.core import BackupInstance
from minarca_client.core.compat import IS_MAC
from minarca_client.locale import _
from minarca_client.ui import tkvue

from .side_pannel import SidePanel  # noqa

logger = logging.getLogger(__name__)


class BackupLogs(tkvue.Component):
    template = """
<Frame pack="expand:1; fill:both">
    <SidePanel is-remote="{{is_remote}}" text="Get detailed information about you last backup execution." step="2" maximum="3" pack="side:left; fill:y" />
    <Separator orient="vertical" pack="side:left; fill:y" />

    <!-- Form -->
    <Frame style="white.TFrame" padding="50" pack="expand:1; fill:both" >

        <Frame style="white.TFrame" pack="fill:x; pady:0 20">
            <Label text="Backup logs" style="h3.info.white.TLabel" pack="fill:x; side:left"/>
            <Label text="{{ last_backup_text }}"
                image="{{ 'check-circle-fill-success' if last_backup_success else 'exclamation-triangle-fill-warning' }}"
                style="default.white.TLabel"
                compound="right"
                pack="fill:x; side:right" />
        </Frame>

        <Label text="{{error_details}}" style="white.warning.TLabel" wrap="1" pack="fill:x; pady:0 15" padding="12" visible="{{error_details}}" />

        <Frame style="white.TLabelframe" pack="expand:1; fill:both; pady:0 20" padding="1">
            <Scrollbar id="scrollbar" pack="side:right; fill:y;"/>
            <Text id="logview" pack="fill:both; expand:1;" borderwidth="0" wrap="none" height="2" />
        </Frame>

        <!-- Button -->
        <Frame style="white.TFrame" pack="fill:x">
            <Button text="Back" command="{{cancel}}" style="default.TButton" pack="side:left; padx:0 10;" cursor="hand2" />
        </Frame>
    </Frame>
</Frame>
"""
    instance = None
    status = tkvue.state(None)
    is_remote = tkvue.state(None)

    def __init__(self, master=None, backup=None, instance=None):
        assert backup
        assert instance and isinstance(instance, BackupInstance)
        # Initialise the state.
        self.instance = instance
        self.status.value = self.instance.status
        self.is_remote.value = self.instance.is_remote()
        # Create the view
        super().__init__(master)
        # Make text widget readonly
        self.logview.bind("<Key>", lambda e: "break")
        # Bind text widget with scrollbar
        self.logview.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.configure(command=self.logview.yview)
        # Bind command for copy
        self.logview.bind("<Control-c>", self._copy_text)
        if IS_MAC:
            self.logview.bind("<Button-2>", self._show_popup_menu)
            self.logview.bind("<Control-1>", self._show_popup_menu)
        else:
            self.logview.bind("<Button-3>", self._show_popup_menu)
        # Register a task to read log file.
        self._readlogs_task = self.get_event_loop().create_task(self._readlogs(instance))
        self.root.bind('<Destroy>', self._cancel_tasks, add="+")

    def _copy_text(self, event=None):
        """
        Copy selected text to clipboard
        """
        text_widget = self.logview.selection_get()
        self.root.clipboard_clear()
        self.root.clipboard_append(text_widget)

    def _show_popup_menu(self, event):
        """
        Show context menu to copy text
        """
        menu = tkinter.Menu(self.logview, tearoff=0)
        menu.add_command(label=_("Copy"), command=self._copy_text)
        menu.tk_popup(event.x_root, event.y_root)

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._readlogs_task:
            self._readlogs_task.cancel()

    async def _readlogs(self, instance):
        try:
            action = self.instance.status.action
            if action == 'backup':
                fn = self.instance.backup_log_file
            elif action == 'restore':
                fn = self.instance.restore_log_file
            else:
                return
            try:
                with open(fn, 'r') as f:
                    self.logview.insert('end', f.read())
            except IOError:
                pass  # Do nothing if the file cannot be open.
        except Exception:
            logger.exception('problem occured while reading backup logs')

    @tkvue.computed_property
    def last_backup_text(self):
        """Return the last backup description."""
        if self.status.value and self.status.value.lastdate:
            value = self.status.value.lastdate.strftime("%a, %d %b %Y %H:%M")
        else:
            value = _('No backup yet')
        return _('Last backup: %s') % value

    @tkvue.computed_property
    def last_backup_success(self):
        """Return corresponding icon depending of the last backup status."""
        return self.status.value and self.status.value.current_status in ['SUCCESS', 'RUNNING']

    @tkvue.computed_property
    def error_details(self):
        status = self.status.value
        if status is None:
            return None
        return status.details

    @tkvue.command
    def cancel(self):
        # Go back to dashboard
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view('DashboardView')
