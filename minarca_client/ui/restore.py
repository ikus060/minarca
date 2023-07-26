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
from minarca_client.core.config import Pattern
from minarca_client.core.exceptions import BackupError, RunningError
from minarca_client.locale import _
from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


class RestorePatternDialog(tkvue.Component):
    template = pkg_resources.resource_string('minarca_client.ui', 'templates/restore_pattern.html').decode("utf-8")

    def __init__(self, *args, **kwargs):
        self.data = tkvue.Context(
            {
                'patterns': [],
                'confirm': False,
                'check_button_text': lambda item: _('Restore') if item.include else _('Ignore'),
            }
        )
        super().__init__(*args, **kwargs)
        self.root.bind('<Return>', self.return_event)
        self.root.bind('<Key-Escape>', self.cancel_event)
        # Asynchronously load pattern from backup.
        self.root.after(1, self._fetch_patterns)

    def return_event(self, event=None):
        # Quit this windows
        if self.data.patterns:
            self.root.destroy()
        else:
            self.root.bell()

    def cancel_event(self, event=None):
        # Remove password value
        self.data.patterns = []
        # Close this windows
        self.root.destroy()

    async def modal(self):
        """
        Make this dialog modal.
        """
        self.root.protocol("WM_DELETE_WINDOW", self.cancel_event)  # intercept close button

        # Dialog boxes should be transient with respect to their parent,
        # so that they will always stay on top of their parent window.  However,
        # some window managers will create the window as withdrawn if the parent
        # window is withdrawn or iconified.  Combined with the grab we put on the
        # window, this can hang the entire application.  Therefore we only make
        # the dialog transient if the parent is viewable.
        if self.root.master:
            toplevel = self.root.master.winfo_toplevel()
            if toplevel.winfo_viewable():
                self.root.transient(toplevel)  # dialog window is related to main
        self.root.tk.eval('tk::PlaceWindow %s' % self.root)
        self.root.wait_visibility()  # can't grab until window appears, so we wait
        self.root.grab_set()  # ensure all input goes to our window
        # The following replace call to `self.root.wait_window()`
        try:
            while self.root.winfo_exists():
                await asyncio.sleep(0.01)
        except tkinter.TclError:
            return

    def toggle_pattern(self, item):
        """
        Toggle Restore/Ignore of the given pattern.
        """
        patterns = list(self.data.patterns)
        if item in patterns:
            new_pattern = Pattern(not item.include, item.pattern, item.comment)
            idx = patterns.index(item)
            patterns[idx] = new_pattern
            self.data.patterns = patterns

    def _fetch_patterns(self):
        self.get_event_loop().create_task(self._fetch_patterns_task())

    async def _fetch_patterns_task(self):
        backup = Backup()
        # Keep copy of original patterns.
        bak_patterns = None
        orig_status = backup.get_status()
        orig_patterns = backup.get_patterns()
        try:
            # First, we need to check if Minarca config could be restore from backup.
            patterns = [Pattern(True, backup.patterns_file, None)]
            await self.get_event_loop().run_in_executor(None, backup.restore, None, patterns)
            bak_patterns = backup.get_patterns()
        except RunningError:
            tkinter.messagebox.showwarning(
                parent=self.root,
                icon='warning',
                title=_('Operation already in Progress'),
                message=_('Operation already in Progress'),
                detail=_(
                    'A restore or backup operation is currently running. Please wait for the operation to complete before initiating a full recovery. Initiating a recovery while a restore or backup is in progress may lead to data inconsistencies or errors.'
                ),
            )
            self.cancel_event()
            return
        except BackupError:
            # If not, let the user know previous config was not backup.
            response = tkinter.messagebox.askyesno(
                parent=self.root,
                title=_('Minarca Configuration Retrieval'),
                message=_("Could not retrieve Minarca Configuration. Do you want to continue?"),
                detail=_(
                    "Retrieval of Minarca configuration operation has encountered an error or has failed to locate the configuration file. Continuing without retrieving the Minarca configuration require you to manually verify the selected files otherwise it may result in potential data loss during the restore process."
                ),
            )
            if not response:
                # Operation cancel by user
                self.cancel_event()
                return
        finally:
            # Restore original patterns and status.
            orig_patterns.save()
            orig_status.save()

        # If original patterns could be restore. Use it.
        patterns = bak_patterns or orig_patterns

        # Keep only include pattern as we cant restore excluded files.
        self.data.patterns = [p for p in patterns if p.include and not p.is_wildcard()]


class RestoreView(tkvue.Component):
    template = pkg_resources.resource_string('minarca_client.ui', 'templates/restore.html').decode("utf-8")

    def __init__(self, *args, **kwargs):
        self.backup = Backup()
        super().__init__(*args, **kwargs)

    def partial_restore(self):
        """
        Redirect user to web interface.
        """
        remote_url = self.backup.get_repo_url()
        webbrowser.open(remote_url)

    def full_restore(self):
        self.get_event_loop().create_task(self.full_restore_task())

    async def full_restore_task(self):
        """
        Proceed with full restore.
        """
        # Based on Pattern list, prompt user for folders to be restored
        dlg = RestorePatternDialog(self.root)
        await dlg.modal()
        patterns = [p for p in dlg.data.patterns if p.include]
        if not patterns:
            # Operation cancel by user
            return

        # If user select at least one pattern/folder, proceed with restore.
        self.backup.start('restore', force=True, patterns=patterns)
