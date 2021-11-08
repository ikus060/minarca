# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging
import tkinter
import tkinter.filedialog
import tkinter.simpledialog

import pkg_resources
from minarca_client.core import Backup
from minarca_client.core.compat import get_home
from minarca_client.core.config import Pattern
from minarca_client.locale import _
from minarca_client.ui import tkvue

logger = logging.getLogger(__name__)


class PatternsView(tkvue.Component):
    template = pkg_resources.resource_string('minarca_client.ui', 'templates/patterns.html').decode("utf-8")

    def __init__(self, *args, **kwargs):
        self.backup = Backup()
        self.data = tkvue.Context({
            'patterns': self.backup.get_patterns(),
            'check_button_text': lambda item: _('Included') if item.include else _('Excluded'),
        })
        super().__init__(*args, **kwargs)

    def remove_pattern(self, item):
        """
        Remove the given pattern.
        """
        self.patterns = self.backup.get_patterns()
        if item in self.patterns:
            self.patterns.remove(item)
            self.backup.set_patterns(self.patterns)
            self.data.patterns = self.patterns

    def toggle_pattern(self, item):
        """
        Toggle include/exclude flag of the given pattern.
        """
        self.patterns = self.backup.get_patterns()
        if item in self.patterns:
            new_pattern = Pattern(not item.include,
                                  item.pattern, item.comment)
            idx = self.patterns.index(item)
            self.patterns[idx] = new_pattern
            self.backup.set_patterns(self.patterns)
            self.data.patterns = self.patterns

    def add_file_pattern(self):
        # Prompt user to select one or more file.
        filenames = tkinter.filedialog.askopenfilenames(
            initialdir=get_home(),
            parent=self.root.winfo_toplevel(),
        )
        if not filenames:
            # Operation cancel by user
            return
        # Check if the file is already in the pattern list.
        self.patterns = self.backup.get_patterns()
        existing_filenames = [p.pattern for p in self.patterns]
        for fn in filenames:
            if fn in existing_filenames:
                continue
            p = Pattern(True, fn, None)
            self.patterns.append(p)
            # Save the pattern file
            self.backup.set_patterns(self.patterns)
            # Add pattern to the list.
            self.data.patterns = self.patterns

    def add_folder_pattern(self):
        folder = tkinter.filedialog.askdirectory(
            initialdir=get_home(),
            title=_('Add Folder Pattern'),
            # message=_('Select folder(s) to be include or exclude from backup.'),
            parent=self.root.winfo_toplevel(),
        )
        if not folder:
            # Operation cancel by user
            return
        self.add_custom_pattern(folder)

    def add_custom_pattern(self, pattern=None):
        if pattern is None:
            pattern = tkinter.simpledialog.askstring(
                parent=self.root.winfo_toplevel(),
                title=_("Add custom pattern"),
                prompt=_("You may provide a custom pattern to include or exclude file.\nCustom pattern may include wildcard `*` or `?`."))
            # TODO Add more validation here.
            if not pattern:
                # Operation cancel by user
                return
        # Check if the file is already in the pattern list.
        self.patterns = self.backup.get_patterns()
        existing_filenames = [p.pattern for p in self.patterns]
        if pattern in existing_filenames:
            return
        p = Pattern(True, pattern, None)
        self.patterns.append(p)
        # Save the pattern file
        self.backup.set_patterns(self.patterns)
        # Add pattern to the list.
        self.data.patterns = self.patterns
