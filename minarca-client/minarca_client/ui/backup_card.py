# Copyleft (C) 2023 IKUS Software. All lefts reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging
import tkinter.messagebox

import humanfriendly

from minarca_client.core import BackupInstance
from minarca_client.core.compat import watch_file
from minarca_client.locale import _
from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


class BackupCard(tkvue.Component):
    template = """
<Frame style="white.TLabelframe" padding="30" columnconfigure-weight="0 1 0 0">

    <!-- Header -->
    <Label image="{{backup_icon}}" style="white.TLabel" grid="row:0; column:0; rowspan:2; sticky:w; padx:0 5"/>

    <Label text="{{ _('Remote backup') if is_remote else _('Local backup') }}"
        style="sm.info.white.TLabel"
        grid="row:0; column:1; sticky:ws" />
    <Label text="{{ settings and settings.repositoryname }}" style="white.TLabel" grid="row:1; column:1; sticky:wn"/>

    <Checkbutton id="pause_btn" command="{{toggle_pause}}" selected="{{ settings and settings.pause_until is None }}" text="{{ pause_text }}"
        style="info.white.Roundtoggle.TCheckbutton" cursor="hand2" grid="row:0; column:2; rowspan:2; columnspan:3; sticky:ne"/>

    <!-- Quota -->
    <Progressbar value="{{disk_usage.get('used', 0)}}" maximum="{{ disk_usage.get('total', 10) }}" style="info.Horizontal.TProgressbar" grid="row:2; column:0; columnspan:4; sticky:we; pady:20 8" />
    <Label text="{{ disk_used_text }}" style="xs.light.white.TLabel" grid="row:3; column:0; columnspan:2; sticky:w"/>
    <Label text="{{ disk_total_text }}" style="xs.light.white.TLabel" grid="row:3; column:2; columnspan:2; sticky:e"/>

    <!-- Start / Stop backup -->
    <Separator grid="row:4; column:0; columnspan:4; sticky:we; pady:12 0"/>
    <Button text="{{ _('Stop running backup') if is_running else _('Start Backup now') }}"
        style="{{ 'light-warning.stop-circle.TListitem' if is_running else 'light-info.play-circle.TListitem' }}"
        image="{{ 'spinner-16' if is_running else None }}"
        compound="right"
        command="{{stop_start_backup}}"
        padding="10"
        grid="row:5; column:0; columnspan:3; sticky:nsew;"
        cursor="hand2" />

    <!-- Last backup -->
    <Button text="{{ last_backup_text }}"
        style="{{ 'white.TListitem' if last_backup_success else 'light-warning.TListitem' }}"
        image="{{ 'check-circle-fill-success' if last_backup_success else 'exclamation-triangle-fill-warning' }}"
        compound="right"
        command="{{ backup_logs }}"
        padding="10"
        grid="row:7; column:0; columnspan:3; sticky:nsew;"
        cursor="hand2">
            <Tooltip text="{{last_backup_tooltip}}" width="55"/>
    </Button>

    <!-- Server connection -->
    <Button text="{{ _('Server connection') if is_remote else _('Local connection') }}"
        command="{{ backup_connection }}"
        style="{{ 'white.TListitem' if test_connection_success else 'light-warning.TListitem' }}"
        image="{{ test_connection_icon }}"
        compound="right"
        padding="10" grid="row:9; column:0; columnspan:3; sticky:nsew;"
        cursor="hand2">
            <Tooltip text="{{test_connection_text}}" width="55"/>
    </Button>

    <!-- Backup settings -->
    <Button text="Backup configuration" command="{{backup_settings}}" style="white.TListitem" padding="10" grid="row:11; column:0; columnspan:3; sticky:nsew;" cursor="hand2"/>

    <!-- Backup patterns -->
    <Button text="File selection" command="{{backup_patterns}}" style="white.TListitem" padding="10" grid="row:13; column:0; columnspan:3; sticky:nsew;" cursor="hand2"/>

    <!-- Restore -->
    <Button text="Restore backup" style="white.TListitem" padding="10" grid="row:15; column:0; columnspan:3; sticky:nsew;" cursor="hand2"/>

    <!-- Restore -->
    <Button text="Restore backup" style="white.TListitem" padding="10" grid="row:15; column:0; columnspan:3; sticky:nsew;" cursor="hand2"/>
</Frame>
"""
    instance = None
    is_remote = tkvue.state(True)
    settings = tkvue.state(None)
    status = tkvue.state(None)
    disk_usage = tkvue.state({'used': 0, 'total': -1})
    test_connection = tkvue.state(None)

    _status_task = None
    _settings_task = None
    _disk_usage_task = None
    _test_connection_task = None

    def __init__(self, master=None):
        super().__init__(master)
        self.root.bind('<Destroy>', self._cancel_tasks, add="+")

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._status_task:
            self._status_task.cancel()
        if self._settings_task:
            self._settings_task.cancel()
        if self._disk_usage_task:
            self._disk_usage_task.cancel()
        if self._test_connection_task:
            self._test_connection_task.cancel()

    async def _watch_status(self, instance):
        # Asynchronously watch the status files for changes.
        # Update the TKVuew data context whenever it changes.
        """
        Special implementation of awatch forcing update after 5 seconds of inativity when running.
        """
        try:
            status = instance.status
            async for unused in watch_file(status, timeout=status.RUNNING_DELAY):
                self.status.value.reload()
                self.status.notify()
        except Exception:
            logger.exception('problem occured while watching status')

    async def _watch_settings(self, instance):
        # Asynchronously watch the status files for changes.
        # Update the TKVuew data context whenever it changes.
        try:
            settings = instance.settings
            async for unused in watch_file(settings):
                self.settings.value.reload()
                self.settings.notify()
        except Exception:
            logger.exception('problem occured while watching settings')

    async def _get_disk_usage(self, instance):
        # Get disk usage in different thread since connection error might block request.
        try:
            value = await self.get_event_loop().run_in_executor(None, instance.get_disk_usage)
        except Exception:
            # Network issue or dis not connected.
            logger.warn('problem occured while retreiving disk usage', exc_info=1)
            value = None
        # Update state.
        if value:
            self.disk_usage.value = {'used': value[0], 'total': value[1]}
        else:
            self.disk_usage.value = {'used': 0, 'total': 0}

    async def _test_connection(self, instance):
        # Test connectivity with remote server every 5 secs
        while True:
            try:
                await self.get_event_loop().run_in_executor(None, instance.test_connection)
                self.test_connection.value = True
            except Exception as e:
                # Exception raise - either server is not responding or disk is not connected.
                self.test_connection.value = e
            await asyncio.sleep(5)

    @tkvue.attr('instance')
    def set_instance(self, instance):
        assert isinstance(instance, BackupInstance)
        # Destroy previous task
        self._cancel_tasks()
        # Schedule update asynchronously.
        self._status_task = self.get_event_loop().create_task(self._watch_status(instance))
        self._settings_task = self.get_event_loop().create_task(self._watch_settings(instance))
        self._disk_usage_task = self.get_event_loop().create_task(self._get_disk_usage(instance))
        self._test_connection_task = self.get_event_loop().create_task(self._test_connection(instance))
        # Update status
        self.instance = instance
        self.is_remote.value = self.instance.is_remote()
        self.status.value = instance.status
        self.settings.value = instance.settings

    @tkvue.computed_property
    def backup_icon(self):
        if self.is_remote.value:
            return 'remote-backup-logo-64'
        else:
            return 'local-backup-logo-64'

    @tkvue.computed_property
    def pause_text(self):
        if self.settings.value and self.settings.value.pause_until:
            return _('Paused')
        else:
            return _('Active')

    @tkvue.computed_property
    def disk_used_text(self):
        used = self.disk_usage.value.get('used', 0)
        total = self.disk_usage.value.get('total', 0)
        if total < 0:
            return _('Calculating disk usage')  # Initial value
        elif total == 0:
            return _('Cannot determine disk usage')
        return _('Used space %s') % humanfriendly.format_size(used, binary=1)

    @tkvue.computed_property
    def disk_total_text(self):
        total = self.disk_usage.value.get('total', 0)
        humanfriendly.format_size(total)
        if total <= 0:
            return None
        return _('Total space %s') % humanfriendly.format_size(total, binary=1)

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
    def last_backup_tooltip(self):
        status = self.status.value
        if status is None:
            return None
        return status.details

    @tkvue.computed_property
    def is_running(self):
        return self.status.value and self.status.value.current_status in ['RUNNING', 'STALE']

    @tkvue.computed_property
    def test_connection_success(self):
        # Success if test server is None (undefined) or True
        return self.test_connection.value is None or self.test_connection.value is True

    @tkvue.computed_property
    def test_connection_icon(self):
        # Return text representation of the test server
        if self.test_connection.value is None:
            return None
        elif self.test_connection.value is True:
            return 'check-circle-fill-success'
        else:
            return 'exclamation-triangle-fill-warning'

    @tkvue.computed_property
    def test_connection_text(self):
        # Return text representation of the test server
        if self.test_connection.value is None:
            return _('Verifying connection...')
        elif self.test_connection.value is True:
            return _('Connection healthy')
        else:
            # This is an exception.
            return str(self.test_connection.value)

    @tkvue.command
    def toggle_pause(self):
        """Called to toggle backup pause feature. Will confirm with user before."""
        # Check current pause status
        pause_until = self.instance.settings.pause_until
        if pause_until:
            delay = 0
        else:
            # Confirm with user
            if not tkinter.messagebox.askyesno(
                parent=self.root,
                title=_('Pause Backup Job Confirmation'),
                message=_('Are you sure you want to pause the backup job?'),
                detail=_(
                    'Pausing the backup job will temporarily suspend the ongoing backup process for the next 12 hours. This action may affect the availability of recent data restore points and introduce delays in the backup schedule. Please confirm your intention before proceeding.'
                ),
            ):
                # Cancel by user
                delay = 0
            else:
                # Pause backup
                delay = 12
        # Store change in instance settings
        self.instance.pause(delay=delay)
        # Manually update interface to avoid delay.
        self.settings.notify()

    @tkvue.command
    def stop_start_backup(self):
        if not self.instance.is_running():
            try:
                self.instance.start(force=True)
            except Exception as e:
                logger.exception('fail to start backup')
                tkinter.messagebox.showerror(
                    parent=self.root,
                    title=_("Start Backup"),
                    message=_("A problem occurred when trying to start the backup process."),
                    detail=_("This usually indicate a problem with the installation. Try re-installing Minarca Backup.")
                    + '\n'
                    + str(e),
                )
        else:
            try:
                self.instance.stop()
            except Exception as e:
                logger.exception('fail to stop')
                tkinter.messagebox.showerror(
                    parent=self.root,
                    title=_("Stop process"),
                    message=_("A problem occurred when trying to stop the process."),
                    detail=str(e),
                )

    @tkvue.command
    def backup_logs(self):
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view('BackupLogs', instance=self.instance)

    @tkvue.command
    def backup_connection(self):
        if self.is_remote.value:
            toplevel = self.root.winfo_toplevel()
            toplevel.set_active_view('BackupConnectionRemote', instance=self.instance)
        else:
            toplevel = self.root.winfo_toplevel()
            toplevel.set_active_view('BackupConnectionLocal', instance=self.instance)

    @tkvue.command
    def backup_settings(self):
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view('BackupSettings', instance=self.instance)

    @tkvue.command
    def backup_patterns(self):
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view('BackupPatterns', instance=self.instance)
