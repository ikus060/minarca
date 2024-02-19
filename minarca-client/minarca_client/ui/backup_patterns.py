# Copyleft (C) 2023 IKUS Software. All lefts reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging
import tkinter.filedialog
import tkinter.messagebox

from minarca_client.core import BackupInstance
from minarca_client.core.compat import IS_WINDOWS, get_home
from minarca_client.core.config import Pattern, Patterns
from minarca_client.locale import _
from minarca_client.ui import tkvue

from .side_pannel import SidePanel  # noqa

logger = logging.getLogger(__name__)


class BackupPatterns(tkvue.Component):
    template = """
<Frame pack="expand:1; fill:both">
    <SidePanel create="{{create}}" is-remote="{{is_remote}}" text="Select files and folders to include in backup." step="1" maximum="3" pack="side:left; fill:y" />
    <Separator orient="vertical" pack="side:left; fill:y" />

    <!-- Form -->
    <Frame style="white.TFrame" padding="50" pack="expand:1; fill:both">
        <Label text="File selection" style="h3.info.white.TLabel" pack="fill:x; pady:0 20"/>

        <Frame style="white.TFrame" pack="fill:x; pady:0 20">
            <Button text="Add folder" command="{{add_folder_pattern}}" style="sm.secondary.TButton" pack="side:left; padx:0 10; anchor:w"/>
            <Button text="Add file" command="{{add_file_pattern}}" style="sm.secondary.TButton" pack="side:left; padx:0 10; anchor:w"/>
            <!-- Formula -->
            <Label text="Formula" image="question-circle-fill" compound="right" style="sm.default.white.TLabel" pack="side:left; expand:1; fill:x; anchor:e; padx:0 10" anchor="e">
                <ToolTip text="Question mark (?) matches any single character, Wildcard (*) matches any characters, Double Wildcard (**) match any path. Example: '**/*.txt' matches all '.txt' files." width="55"/>
            </Label>
            <Entry textvariable="{{ custom_pattern }}" pack="side:left; anchor:w" />
            <Button text="Add" command="{{add_custom_pattern}}" style="sm.secondary.TButton" width="3" pack="side:left; anchor:w" state="{{ '!disabled' if custom_pattern else 'disabled' }}"/>
        </Frame>

        <Frame style="white.TLabelframe" pack="fill:both; expand:1; pady:0 20" padding=2>
            <ScrolledFrame style="white.TFrame" pack="fill:both; expand:1;">
                <Frame for="{{item in patterns}}" style="white.TFrame" pack="{{ 'fill:x; pady:20 2; padx:20; expand:1' if loop_idx==0 else 'fill:x; pady:2; padx:20; expand:1' }}" >
                    <Button style="dark.white.TLink" command="{{remove_pattern(item)}}" pack="side:left" image="trash" cursor="hand2">
                        <ToolTip text="Remove pattern" />
                    </Button>
                    <Label text="{{item.comment or item.pattern}}" style="dark.white.TLabel" pack="side:left; padx:15">
                        <ToolTip text="{{item.pattern}}" />
                    </Label>
                    <Checkbutton pack="side:right" command="{{toggle_pattern(item)}}" text="{{ _('Include') if item.include else _('Exclude') }}"
                        style="default.white.Roundtoggle.TCheckbutton" width="10" selected="{{ item.include }}" cursor="hand2" />
                </Frame>
            </ScrolledFrame>
        </Frame>

        <!-- Button -->
        <Frame style="white.TFrame" pack="fill:x">
            <Button text="Cancel" command="{{cancel}}" style="default.TButton" pack="side:left; padx:0 10;" cursor="hand2" />
            <Button text="{{ _('Next') if create else _('Save') }}" command="{{save}}" style="info.TButton" pack="side:left" cursor="hand2" />
            <Button text="Restore to default" command="{{reset_pattern}}" style="white.TLink" pack="side:right;anchor:e" cursor="hand2"/>
        </Frame>
    </Frame>
</Frame>
"""
    is_remote = tkvue.state(True)
    create = tkvue.state(False)
    patterns = tkvue.state([])
    custom_pattern = tkvue.state("")

    # Only for Windows
    show_run_if_logged_out = tkvue.state(IS_WINDOWS)
    run_if_logged_out = tkvue.state(False)

    def __init__(self, master=None, backup=None, instance=None, create=False):
        """Edit or create backup configuration for the given instance"""
        assert backup
        assert instance and isinstance(instance, BackupInstance)
        # Initialise the state.
        self.instance = instance
        self.create.value = create
        self.is_remote.value = self.instance.is_remote()
        self.patterns.value = list(self.instance.patterns)
        # Create the view
        super().__init__(master)

    def _add_pattern(self, pattern):
        # Check if the file is already in the pattern list.
        existing_filenames = [p.pattern for p in self.patterns.value]
        if pattern in existing_filenames:
            return
        # Add pattern to the list.
        self.patterns.value.append(Pattern(True, pattern, None))
        self.patterns.notify()

    @tkvue.command
    def add_folder_pattern(self):
        folder = tkinter.filedialog.askdirectory(
            initialdir=get_home(),
            title=_('Add Folder Pattern'),
            parent=self.root.winfo_toplevel(),
            mustexist=True,
        )
        if not folder:
            # Operation cancel by user
            return
        self._add_pattern(folder)

    @tkvue.command
    def add_file_pattern(self):
        # Prompt user to select one or more file.
        filenames = tkinter.filedialog.askopenfilenames(
            initialdir=get_home(),
            title=_('Add File Pattern'),
            parent=self.root.winfo_toplevel(),
        )
        if not filenames:
            # Operation cancel by user
            return
        for fn in filenames:
            self._add_pattern(fn)

    @tkvue.command
    def add_custom_pattern(self):
        if not self.custom_pattern.value:
            return
        self._add_pattern(self.custom_pattern.value)

    @tkvue.command
    def remove_pattern(self, item):
        """
        Remove the given pattern.
        """
        if item in self.patterns.value:
            self.patterns.value.remove(item)
            self.patterns.notify()

    @tkvue.command
    def toggle_pattern(self, item):
        """
        Toggle include/exclude flag of the given pattern.
        """
        if item in self.patterns.value:
            idx = self.patterns.value.index(item)
            self.patterns.value[idx] = Pattern(not item.include, item.pattern, item.comment)
            self.patterns.notify()

    @tkvue.command
    def reset_pattern(self):
        """
        Called when user click to reset patterns.
        """
        defaults = Patterns.defaults()
        self.patterns.value = defaults

    @tkvue.command
    def cancel(self):
        # In create mode, destroy the configuration and go to dashboard.
        if self.create.value:
            self.instance.forget()
        toplevel = self.root.winfo_toplevel()
        toplevel.set_active_view('DashboardView')

    @tkvue.command
    def save(self):
        # Save Pattern to file
        p = self.instance.patterns
        p.clear()
        p.extend(self.patterns.value)
        p.save()
        # In create mode, start the backup process and go to backup settings.
        if self.create.value:
            toplevel = self.root.winfo_toplevel()
            toplevel.set_active_view('BackupSettings', instance=self.instance, create=True)
        else:
            toplevel = self.root.winfo_toplevel()
            toplevel.set_active_view('DashboardView')
