# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDListItem

from minarca_client.core import BackupInstance
from minarca_client.core.compat import get_home
from minarca_client.core.pattern import Pattern, Patterns
from minarca_client.dialogs import file_dialog, folder_dialog
from minarca_client.locale import _
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)


Builder.load_string(
    '''
<PatternItem>:
    divider: True
    ripple_effect: False
    -height: "56dp"

    MDListItemLeadingIcon:
        icon: "folder-plus-outline" if root.include else "folder-minus-outline"

    MDListItemHeadlineText:
        text: root.comment
        adaptive_height: False
        -height: self.texture_size[1] if root.comment else 0

    MDListItemSupportingText:
        text: root.pattern

    MDIconButton:
        icon: "trash-can-outline"
        on_release: root.on_delete(root.item)

<BackupPatterns>:
    orientation: "horizontal"
    md_bg_color: self.theme_cls.backgroundColor

    SidePanel:
        is_remote: root.is_remote
        create: root.create
        text: _("Select the files and folders you want to back up.")
        step: 2

    MDBoxLayout:
        orientation: "vertical"
        padding: "50dp"
        spacing: "20dp"

        CLabel:
            text: _("File Selection")
            font_style: "Title"
            role: "small"
            text_color: self.theme_cls.primaryColor

        MDTabsSecondary:
            id: tabs
            indicator_height: "3dp"

            MDTabsItemSecondary:
                id: include_tab
                on_release: root.include = True

                MDTabsItemIcon:
                    icon: "plus-circle-multiple-outline"

                MDTabsItemText:
                    text: _('Files included')

            MDTabsItemSecondary:
                id: exclude_tab
                on_release: root.include = False

                MDTabsItemIcon:
                    icon: "minus-circle-multiple-outline"

                MDTabsItemText:
                    text: _('Files excluded')

            MDDivider:

        MDBoxLayout:
            orientation: "horizontal"
            spacing: "10dp"
            adaptive_height: True

            CButton:
                text: _('Add file') if root.include else _('Exclude file')
                role: "small"
                on_release: root.add_file_pattern()

            CButton:
                text: _('Add folder') if root.include else _('Exclude folder')
                role: "small"
                on_release: root.add_folder_pattern()

            CBoxLayout:
                orientation: "horizontal"
                adaptive_height: True
                # Disable custom pattern on "include tab"
                display: not root.include
                TextInput:
                    text: root.custom_pattern
                    on_text: root.custom_pattern = self.text
                    hint_text: _("File extention (e.g.: *.txt)")
                    multiline: False
                    # Change style of TextInput.
                    background_color: app.theme_cls.surfaceColor
                    text_color: app.theme_cls.onSurfaceColor
                    background_normal: ""
                    background_active: ""
                    canvas.after:
                        Color:
                            rgba: app.theme_cls.onSurfaceColor
                        Line:
                            rectangle: [self.x, self.y, self.width, self.height]
                            width: 1

                CButton:
                    text: _('Exclude')
                    on_release: root.add_custom_pattern()
                    disable: not root.custom_pattern
                    role: "small"

        CCard:
            padding: "1dp"

            RecycleView:
                viewclass: "PatternItem"
                data: root.sorted_patterns

                RecycleBoxLayout:
                    spacing: "1dp"
                    padding: "0dp"
                    default_size: None, "56dp"
                    default_size_hint: 1, None
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height

        MDBoxLayout:
            orientation: "horizontal"
            spacing: "10dp"
            padding: (0, "30dp", 0 , 0)
            adaptive_height: True

            CButton:
                id: btn_cancel
                text: _('Cancel')
                on_release: root.cancel()
                theme_bg_color: "Custom"
                md_bg_color: self.theme_cls.inverseSurfaceColor

            CButton:
                text: _('Next') if root.create else _('Save')
                on_release: root.save()

            Widget:

            CButton:
                text: _('Restore to default')
                role: "small"
                style: "text"
                on_release: root.reset_pattern()

'''
)


class PatternItem(MDListItem):
    item = ObjectProperty()
    on_delete = None

    @alias_property(bind=['item'])
    def include(self):
        return bool(self.item and self.item.include)

    @alias_property(bind=['item'])
    def comment(self):
        return (self.item.comment or "") if self.item else ""

    @alias_property(bind=['item'])
    def pattern(self):
        return (self.item.pattern or "") if self.item else ""


class BackupPatterns(MDBoxLayout):
    include = BooleanProperty(True)
    is_remote = BooleanProperty()
    create = BooleanProperty(False)
    patterns = ListProperty(None)
    custom_pattern = StringProperty("")

    _add_folder_task = None
    _add_file_task = None

    def __init__(self, backup=None, instance=None, create=False):
        """Edit or create backup configuration for the given instance"""
        assert backup
        assert instance and isinstance(instance, BackupInstance)
        # Initialise the state.
        self.instance = instance
        self.create = create
        self.is_remote = self.instance.is_remote()
        self.patterns = list(self.instance.patterns)
        # Create the view
        super().__init__()
        # Make the include tabs active
        self.ids['include_tab'].on_release()

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._add_folder_task:
            self._add_folder_task.cancel()
        if self._add_file_task:
            self._add_file_task.cancel()

    @alias_property(bind=['patterns', 'include'])
    def sorted_patterns(self):
        patterns = sorted(
            self.patterns,
            key=lambda p: (
                not p.include,  # Include first.
                p.pattern.startswith('**'),  # Wildcard exclude last.
                len(p.pattern.split('/')),  # Shorter path first.
                p.pattern,  # Then pattern
            ),
        )
        return [{'item': p, "on_delete": self.remove_pattern} for p in patterns if p.include == self.include]

    def _add_pattern(self, pattern):
        # Check if the file is already in the pattern list.
        existing_filenames = [p.pattern for p in self.patterns]
        if pattern in existing_filenames:
            return
        # Add pattern to the list.
        self.patterns.append(Pattern(self.include, pattern, None))

    def add_folder_pattern(self):
        async def _add_folder_pattern():
            folders = await folder_dialog(
                parent=self, title=_('Add folder'), initial_directory=get_home(), multiple_select=True
            )
            for folder in folders:
                self._add_pattern(folder)

        self._add_folder_task = asyncio.create_task(_add_folder_pattern())

    def add_file_pattern(self):
        async def _add_file_pattern():
            # Prompt user to select one or more file.
            filenames = await file_dialog(
                parent=self, title=_('Add file'), multiple_select=True, initial_directory=get_home()
            )
            for fn in filenames:
                self._add_pattern(fn)

        self._add_file_task = asyncio.create_task(_add_file_pattern())

    def add_custom_pattern(self):
        if not self.custom_pattern:
            return
        self._add_pattern(self.custom_pattern)
        self.custom_pattern = ""

    def remove_pattern(self, item):
        """
        Remove the given pattern.
        """
        if item in self.patterns:
            self.patterns.remove(item)

    def reset_pattern(self):
        """
        Called when user click to reset patterns.
        """
        defaults = [p for p in Patterns.defaults() if p.include == self.include]
        existing = [p for p in self.patterns if p.include != self.include]
        self.patterns = defaults + existing

    def cancel(self):
        # In create mode, destroy the configuration and go to dashboard.
        if self.create:
            self.instance.forget()
        App.get_running_app().set_active_view('dashboard.DashboardView')

    def save(self):
        # Save Pattern to file
        p = self.instance.patterns
        p.clear()
        p.extend(self.patterns)
        p.save()
        # In create mode, start the backup process and go to backup settings.
        if self.create:
            App.get_running_app().set_active_view('backup_settings.BackupSettings', instance=self.instance, create=True)
        else:
            App.get_running_app().set_active_view('dashboard.DashboardView')
