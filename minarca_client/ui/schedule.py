# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging
import os
import tkinter.messagebox
import tkinter.simpledialog

import pkg_resources

from minarca_client.core import Backup
from minarca_client.core.compat import IS_WINDOWS
from minarca_client.locale import _
from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


class CredentialDialog(tkvue.Component):
    template = pkg_resources.resource_string('minarca_client.ui', 'templates/credential.html')

    def __init__(self, *args, **kwargs):
        self.data = tkvue.Context(
            {
                'credential_header': pkg_resources.resource_filename(
                    "minarca_client.ui", "theme/credential-header.png"
                ),
                'username': '',
                'password': '',
            }
        )
        super().__init__(*args, **kwargs)
        self.root.bind('<Return>', self.return_event)
        self.root.bind('<Key-Escape>', self.cancel_event)

    def return_event(self, event=None):
        # Quit this windows
        if self.data['password']:
            self.root.destroy()
        else:
            self.root.bell()

    def cancel_event(self, event=None):
        # Remove password value
        self.data['password'] = ''
        # Close this windows
        self.root.destroy()

    def modal(self):
        self.root.protocol("WM_DELETE_WINDOW", self.cancel_event)  # intercept close button
        if self.root.master:
            self.root.transient(self.root.master)  # dialog window is related to main
            self.root.tk.eval('tk::PlaceWindow %s widget %s' % (self.root, self.root.master))
        self.root.wait_visibility()  # can't grab until window appears, so we wait
        self.root.grab_set()  # ensure all input goes to our window
        self.root.wait_window()  # block until window is destroyed


class ScheduleView(tkvue.Component):
    template = pkg_resources.resource_string('minarca_client.ui', 'templates/schedule.html').decode("utf-8")

    def __init__(self, *args, **kwargs):
        self.backup = Backup()
        self.data = tkvue.Context(
            {
                'schedule': self.backup.get_settings('schedule'),
                'show_run_if_logged_out': IS_WINDOWS,
                'run_if_logged_out': IS_WINDOWS and self.backup.scheduler.run_if_logged_out,
                'paused': self.backup.get_settings('pause_until') is not None,
            }
        )
        super().__init__(*args, **kwargs)
        self.data.watch('schedule', self.update_schedule)

    def update_schedule(self, value):
        """
        Called to update the frequency.
        """
        self.backup.set_settings('schedule', value)

    def refresh_run_if_logged_out(self):
        self.data['run_if_logged_out'] = self.backup.scheduler.run_if_logged_out

    def toggle_pause(self):
        """
        Called to toggle backup pause feature. Will confirm with user before.
        """
        # Check current pause status
        pause_until = self.backup.get_settings('pause_until')
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
        # Update interface
        self.backup.pause(delay=delay)
        self.data.paused = self.backup.get_settings('pause_until') is not None

    def toggle_run_if_logged_out(self):
        """
        Called to toggle the "run_if_logged_out" settings.
        """
        # This is only applicable to Windows scheduler.
        if not IS_WINDOWS:
            return
        value = self.backup.scheduler.run_if_logged_out
        if value:
            # If disable, re-schedule the taks with default settings.
            self.backup.schedule_job()
        else:
            # If enabled, prompt user for password.
            dlg = CredentialDialog(master=self.root)
            dlg.data['username'] = os.getlogin()
            dlg.modal()
            if not dlg.data['password']:
                # Operation cancel by user
                return
            try:
                self.backup.schedule_job(run_if_logged_out=(dlg.data['username'], dlg.data['password']))
            except Exception as e:
                tkinter.messagebox.showwarning(
                    parent=self.root,
                    icon='warning',
                    title=_('Task Scheduler'),
                    message=_('Task Scheduler cannot apply your changes.'),
                    detail=str(e),
                )
                # Restore default
                self.backup.schedule_job()
        # Update UI with changes.
        self.root.after(1, self.refresh_run_if_logged_out)
