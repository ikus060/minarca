# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import datetime
import logging

from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDListItem

from minarca_client.core.exceptions import BackupError
from minarca_client.core.instance import BackupInstance, reduce_path
from minarca_client.dialogs import folder_dialog, question_dialog
from minarca_client.locale import _, ngettext
from minarca_client.ui.date_picker import CDatePicker  # noqa
from minarca_client.ui.spinner_overlay import SpinnerOverlay  # noqa
from minarca_client.ui.theme import CButton  # noqa
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)


Builder.load_string(
    '''
<FileItem>
    divider: True
    ripple_effect: False

    MDListItemLeadingIcon:
        icon: root.icon

    MDListItemSupportingText:
        text: root.text

    MDListItemTrailingCheckbox:
        id: stored_state
        checkbox_icon_down: 'checkbox-intermediate' if root.parent_selected else 'checkbox-marked'
        active: root.selected or root.parent_selected
        disabled: root.parent_selected
        on_release: root.toggle_checkbox_state()

<BackupRestoreFiles>:
    orientation: "horizontal"
    md_bg_color: self.theme_cls.backgroundColor

    SidePanel:
        is_remote: root.is_remote
        restore: True
        text: _("When you perform a custom restore, the selected item is restored to a different location selected by you.")

    MDRelativeLayout:

        MDBoxLayout:
            orientation: "vertical"
            padding: "50dp"
            spacing: "15dp"
            pos_hint: {'top': 1}

            CLabel:
                text: _("File selection")
                font_style: "Title"
                role: "small"
                text_color: self.theme_cls.primaryColor

            CLabel:
                text: root.error_message
                text_color: self.theme_cls.onErrorColor
                md_bg_color: self.theme_cls.errorColor
                padding: ("15dp", "12dp")
                display: root.error_message

            CLabel:
                text: root.error_detail
                text_color: self.theme_cls.errorColor
                display: root.error_detail

            CTextField:
                text: root.search
                on_text: root.search = self.text

                MDTextFieldHintText:
                    text: _("Search for files or folders...")

                MDTextFieldTrailingIcon:
                    icon: "magnify"

            RecycleView:
                id: availables
                data: root.file_items
                viewclass: "FileItem"
                selected_files: root.selected_files
                canvas.after:
                    Color:
                        rgba: app.theme_cls.onSurfaceColor
                    Line:
                        rectangle: [self.x, self.y, self.width, self.height]
                        width: 1

                RecycleBoxLayout:
                    spacing: "1dp"
                    padding: "0dp"
                    default_size: None, "56dp"
                    default_size_hint: 1, None
                    orientation: 'vertical'
                    size_hint_y: None
                    height: self.minimum_height
                    key_selection: 'text'

            CCheckbox:
                text: _("Restore files in-place, replacing existing files. I understand this may overwrite data if the destination isn't empty.")
                active: root.in_place
                on_active: root.in_place = self.active
                adaptive_height: True

            MDBoxLayout:
                orientation: "horizontal"
                spacing: "10dp"
                adaptive_height: True

                CButton:
                    id: btn_cancel
                    text: _('Back')
                    on_release: root.cancel()
                    disabled: root.working
                    theme_bg_color: "Custom"
                    md_bg_color: self.theme_cls.inverseSurfaceColor

                CButton:
                    text: _('Restore...')
                    on_release: root.save()
                    disabled: root.working or not root.selected_files

                CLabel:
                    text: root.selected_files_summary
                    shorten: True
                    shorten_from: 'right'
                    pos_hint: {"center_y": .5}

        SpinnerOverlay:
            text: root.working
            display: bool(root.working)
'''
)


class FileItem(RecycleDataViewBehavior, MDListItem):
    rv = None
    data = None
    icon = StringProperty()
    text = StringProperty()
    selected = BooleanProperty(False)
    parent_selected = BooleanProperty(False)

    def refresh_view_attrs(self, rv, index, data):
        self.rv = rv
        self.data = data
        self.parent_selected = any(
            data['text'].startswith(item.get('text', '') + '/') for item in self.rv.selected_files
        )
        self.selected = data in self.rv.selected_files
        return super().refresh_view_attrs(rv, index, data)

    def toggle_checkbox_state(self):
        if self.rv is None:
            return
        if self.parent_selected:
            # Do nothing if already included by parent.
            return
        # Store selection in selected_files
        self.selected = not self.selected
        if self.selected:
            self.rv.selected_files.append(self.data)
        elif self.data in self.rv.selected_files:
            self.rv.selected_files.remove(self.data)
        # Force refresh to account for parent_selected
        self.rv.refresh_from_data()


class BackupRestoreFiles(MDBoxLayout):
    instance = None
    increment = None
    is_remote = BooleanProperty()
    error_message = StringProperty()
    error_detail = StringProperty()
    working = StringProperty()
    search = StringProperty()
    file_items = ListProperty()
    # Item selected by the user.
    selected_files = ListProperty()
    # True to restore at same location
    in_place = BooleanProperty(False)

    _fetch_files_task = None

    def __init__(self, backup=None, instance=None, increment=None):
        assert backup
        assert instance and isinstance(instance, BackupInstance)
        assert increment and isinstance(increment, datetime.datetime)
        # Initialise the state.
        self.instance = instance
        self.increment = increment
        self.is_remote = self.instance.is_remote()
        # Create the view
        super().__init__()
        # Start task to get increments list.
        self.working = _('Please wait. Getting file list...')
        self._fetch_files_task = asyncio.create_task(self._fetch_files(instance))

        # Debounce timer
        self.filter_event = None

    async def _fetch_files(self, instance):
        try:
            file_list = await instance.list_files(self.increment)
            file_items = []
            for fn in file_list:
                file_items.append(
                    {
                        'text': fn,
                        'icon': 'file-outline',
                    }
                )
            self.file_items = file_items
        except BackupError as e:
            logger.warning(str(e), exc_info=1)
            self.error_message = _('Failed to retrieve available files.')
            self.error_detail = str(e)
        except Exception as e:
            logger.exception('unknown exception')
            self.error_message = _('Unknown problem occurred when collecting file list.')
            self.error_detail = str(e)
        finally:
            self.working = ''

    def on_search(self, instance, value):
        """Debounce the search filter updates."""
        if self.filter_event:
            self.filter_event.cancel()  # Cancel the previous scheduled update
        self.filter_event = Clock.schedule_once(lambda dt: self.on_search_update(value), 0.25)

    def on_search_update(self, value):
        # Limit to 100 items
        if self.search:
            filtered_files = [item for item in self.file_items if self.search.lower() in item['text'].lower()]
            self.ids.availables.data = filtered_files[:100]
        else:
            self.ids.availables.data = self.file_items[:100]

    @alias_property(bind=['selected_files'])
    def selected_files_summary(self):
        if self.selected_files:
            paths = reduce_path([item['text'] for item in self.selected_files])
            count = len(paths)
            return ngettext('%s item selected: %s', '%s items selected: %s', count) % (count, ', '.join(paths))
        return _('No item selected')

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._fetch_files_task:
            self._fetch_files_task.cancel()

    def cancel(self):
        # Go back to dashboard
        App.get_running_app().set_active_view(
            'backup_restore_date.BackupRestoreDate', instance=self.instance, increment=self.increment
        )

    def save(self):

        async def _save():
            if self.in_place:
                # Confirm with user to restore
                ret = await question_dialog(
                    parent=self,
                    title=_('Confirm In-Place Restoration'),
                    message=_('Are you sure you want to run a full restoration?'),
                    detail=_(
                        'This action will overwrite all existing files selected with the previous version present in the backup. This action is irreversible and may result in data loss if the destination is not empty.'
                    ),
                )
                folder = None
                if not ret:
                    # Operation cancel by user
                    return
            else:
                # Prompt user where to restore files/folder.
                folder = await folder_dialog(parent=self, title=_('Select a folder where to restore data.'))
                if not folder:
                    # Operation cancel by user
                    return
            # Trigger restore process of the given file to selected folder.
            self.instance.start_restore(
                restore_time=int(self.increment.timestamp()),
                paths=[item['text'] for item in self.selected_files],
                destination=folder,
            )
            # Go to Logs
            App.get_running_app().set_active_view('backup_logs.BackupLogs', instance=self.instance)

        self._select_custom_location_task = asyncio.create_task(_save())
