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

from minarca_client.core import Backup, RunningError
from minarca_client.locale import _
from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


class StatusView(tkvue.Component):
    template = pkg_resources.resource_string('minarca_client.ui', 'templates/status.html')

    def __init__(self, *args, **kwargs):
        self.backup = Backup()
        self.data = tkvue.Context(
            {
                'lastresult': self.backup.get_status('lastresult'),
                'lastdate': self.backup.get_status('lastdate'),
                'details': self.backup.get_status('details'),
                'remoteurl': self.backup.get_settings('remoteurl'),
                'username': self.backup.get_settings('username'),
                'remotehost': self.backup.get_settings('remotehost'),
                'repositoryname': self.backup.get_settings('repositoryname'),
                # Computed variables
                'header_text': self.header_text,
                'status_text': self.status_text,
                'status_text_style': self.status_text_style,
                'start_stop_text': self.start_stop_text,
                'last_backup_text': self.last_backup_text,
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
        lastresult = context.lastresult
        if lastresult == 'SUCCESS':
            return _('Backup is healthy')
        elif lastresult == 'FAILURE':
            return _('Backup failed')
        elif lastresult == 'RUNNING':
            return _('Backup in progress')
        elif lastresult == 'STALE':
            return _('Backup is stale')
        elif lastresult == 'INTERRUPT':
            return _('Backup was interrupted')
        elif lastresult == 'UNKNOWN':
            return _('No backup yet')
        return _('Backup is not healthy')

    @tkvue.computed
    def status_text_style(self, context):
        lastresult = context.lastresult
        if lastresult in ['SUCCESS', 'RUNNING']:
            return 'success'
        elif lastresult in ['UNKNOWN']:
            return 'warning'
        return 'danger'

    @tkvue.computed
    def last_backup_text(self, context):
        lastresult = context['lastresult']
        lastdate = context['lastdate']
        details = context['details']
        if lastresult == 'SUCCESS':
            return _('Complete successfully on %s.') % lastdate
        elif lastresult == 'FAILURE':
            return _('Failed on %s\n%s') % (lastdate, details)
        elif lastresult == 'RUNNING':
            return _('Backup is currently running in background and using system resources.')
        elif lastresult == 'STALE':
            return _('Was started in background on %s, but is currently stale an may use system resources.') % lastdate
        elif lastresult == 'INTERRUPT':
            return (
                _(
                    'Was interrupted on %s. May be caused by loss of connection, computer standby or manual interruption.'
                )
                % lastdate
            )
        return _(
            'Initial backup need to be started. You may take time to configure your parameters and start your initial backup manually.'
        )

    @tkvue.computed
    def remote_text_tooltip(self, context):
        username = context['username']
        remotehost = context['remotehost']
        repositoryname = context['repositoryname']
        return '%s @ %s::%s' % (username, remotehost, repositoryname)

    @tkvue.computed
    def start_stop_text(self, context):
        lastresult = context['lastresult']
        if lastresult in ['RUNNING', 'STALE']:
            return _('Stop backup')
        return _('Start backup')

    def browse_remote(self):
        """
        Open web browser.
        """
        remote_url = self.backup.get_remote_url()
        webbrowser.open(remote_url)

    def _watch_status(self):
        self._task = self.get_event_loop().create_task(self._watch_status_task())

    async def _watch_status_task(self):
        """
        Used to watch the status file and trigger an update whenever the status changes.
        """
        last_status = None
        try:
            while self.root.winfo_exists():
                status = self.backup.get_status()
                if last_status != status:
                    self.data['lastresult'] = status['lastresult']
                    self.data['lastdate'] = status['lastdate']
                    self.data['details'] = status['details']
                # Sleep 500ms
                await asyncio.sleep(0.5)
        except tkinter.TclError:
            # Swallow exception raised when application get destroyed.
            pass

    def start_stop_backup(self):
        try:
            self.backup.start(force=True, fork=True)
        except RunningError:
            self.backup.stop()
        except Exception:
            logger.exception('fail to start backup')
            tkinter.messagebox.showerror(
                parent=self.root,
                title=_("Fail to start backup !"),
                message=_("Fail to start backup !"),
                detail=_(
                    "A fatal error occurred when trying to start the backup process. This usually indicate a problem with the installation. Try re-installing Minarca Backup."
                ),
            )
