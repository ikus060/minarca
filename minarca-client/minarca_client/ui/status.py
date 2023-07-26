# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging
import tkinter
import tkinter.filedialog
import tkinter.simpledialog
import webbrowser

import pkg_resources

from minarca_client.core import Backup
from minarca_client.locale import _
from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


class StatusView(tkvue.Component):
    template = pkg_resources.resource_string('minarca_client.ui', 'templates/status.html')

    def __init__(self, *args, **kwargs):
        self.backup = Backup()
        self.data = tkvue.Context(
            {
                # Status
                'action': self.backup.get_status('action'),
                'lastresult': self.backup.get_status('lastresult'),
                'lastdate': self.backup.get_status('lastdate'),
                'details': self.backup.get_status('details'),
                # settings
                'remoteurl': self.backup.get_settings('remoteurl'),
                'username': self.backup.get_settings('username'),
                'remotehost': self.backup.get_settings('remotehost'),
                'repositoryname': self.backup.get_settings('repositoryname'),
                'pause_until': self.backup.get_settings('pause_until'),
                # Computed variables
                'header_text': self.header_text,
                'status_text': self.status_text,
                'status_text_style': self.status_text_style,
                'last_backup_text': self.last_backup_text,
                'last_backup_text_style': self.last_backup_text_style,
                'remote_text_tooltip': self.remote_text_tooltip,
            }
        )
        super().__init__(*args, **kwargs)
        self.after(500, self._watch_status)

    @tkvue.computed
    def header_text(self, context):
        """
        Return a welcome message
        """
        name = self.backup.get_settings('username')
        if name:
            name = name.capitalize()
        return _('Welcome %s') % name

    @tkvue.computed
    def status_text(self, context):
        """
        Return a human description of backup health base on configuration and last result.
        """
        # If paused, this was a manual operation.
        if context.pause_until:
            return _('Backup paused until %s') % context.pause_until
        status_table = {
            'backup': {
                'SUCCESS': _('Backup is healthy'),
                'FAILURE': _('Backup failed'),
                'RUNNING': _('Backup in progress'),
                'STALE': _('Backup is stale'),
                'INTERRUPT': _('Backup was interrupted'),
                'UNKNOWN': _('No backup yet'),
            },
            'restore': {
                'SUCCESS': _('Restore completed'),
                'FAILURE': _('Restore failed'),
                'RUNNING': _('Restore in progress'),
                'STALE': _('Restore is stale'),
                'INTERRUPT': _('Restore was interrupted'),
            },
        }
        return status_table.get(context.action, {}).get(context.lastresult, _('Backup is not healthy'))

    @tkvue.computed
    def status_text_style(self, context):
        # When paused, make it as warning
        if context.pause_until:
            return 'warning'
        # Otherwise check the status.
        return self.last_backup_text_style(context)

    @tkvue.computed
    def last_backup_text_style(self, context):
        lastresult = context.lastresult
        if lastresult in ['SUCCESS', 'RUNNING']:
            return 'success'
        elif lastresult in ['UNKNOWN']:
            return 'warning'
        return 'danger'

    @tkvue.computed
    def last_backup_text(self, context):
        text_table = {
            'SUCCESS': _('Completed successfully on %s.') % context.lastdate,
            'FAILURE': _('Failed on %s\n%s') % (context.lastdate, context.details),
            'RUNNING': _('Running in background and using system resources.'),
            'STALE': _('Started in background on %s, but is currently stale an may use system resources.')
            % context.lastdate,
            'INTERRUPT': _('Interrupted on %s. May be caused by computer standby or manual interruption.')
            % context.lastdate,
            'UNKNOWN': _('No backup yet'),
        }
        return text_table.get(
            context.lastresult,
            _(
                'Initial backup need to be started. You may take time to configure your parameters and start your initial backup manually.'
            ),
        )

    @tkvue.computed
    def remote_text_tooltip(self, context):
        username = context['username']
        remotehost = context['remotehost']
        repositoryname = context['repositoryname']
        return '%s @ %s::%s' % (username, remotehost, repositoryname)

    def browse_remote(self):
        """
        Open web browser.
        """
        remote_url = self.backup.get_repo_url()
        webbrowser.open(remote_url)

    def _watch_status(self):
        self._task = self.get_event_loop().create_task(self._watch_status_task())

    async def _watch_status_task(self):
        """
        Used to watch the status file and trigger an update whenever the status changes.
        """
        last_status = None
        last_pause_until = None
        try:
            while self.root.winfo_exists():
                status = self.backup.get_status()
                if last_status != status:
                    self.data['action'] = status['action']
                    self.data['lastresult'] = status['lastresult']
                    self.data['lastdate'] = status['lastdate']
                    self.data['details'] = status['details']
                pause_until = self.backup.get_settings('pause_until')
                if last_pause_until != pause_until:
                    self.data['pause_until'] = last_pause_until = pause_until
                # Sleep 500ms
                await asyncio.sleep(0.5)
        except tkinter.TclError:
            # Swallow exception raised when application get destroyed.
            pass

    def start_backup(self):
        try:
            self.backup.start(force=True)
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

    def stop_backup(self):
        try:
            self.backup.stop()
        except Exception as e:
            logger.exception('fail to stop')
            tkinter.messagebox.showerror(
                parent=self.root,
                title=_("Stop process"),
                message=_("A problem occurred when trying to stop the process."),
                detail=str(e),
            )
