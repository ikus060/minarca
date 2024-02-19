# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import datetime
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDListItem

from minarca_client.core import BackupInstance
from minarca_client.core.exceptions import BackupError
from minarca_client.dialogs import folder_dialog
from minarca_client.locale import _
from minarca_client.ui.date_picker import CDatePicker  # noqa
from minarca_client.ui.spinner_overlay import SpinnerOverlay  # noqa
from minarca_client.ui.theme import CButton  # noqa
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)


Builder.load_string(
    '''
<FileItem>
    divider: True
    theme_bg_color: "Custom"
    md_bg_color: self.theme_cls.primaryColor if root.selected else self.theme_cls.transparentColor

    MDListItemLeadingIcon:
        icon: root.icon

    MDListItemSupportingText:
        text: root.text

<BackupRestoreCustom>:
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
                    text: _("Search for files or folder...")

                MDTextFieldTrailingIcon:
                    icon: "magnify"

            CCard:
                padding: "1dp"

                RecycleView:
                    id: recycleview
                    viewclass: "FileItem"
                    data: root.filtered_files

                    SelectableRecycleBoxLayout:
                        spacing: "1dp"
                        padding: "0dp"
                        default_size: None, "56dp"
                        default_size_hint: 1, None
                        orientation: 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        key_selection: 'text'
                        on_selected_nodes: root.on_selected_file_items(*args)

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
                    disabled: root.working or not root.selected_file

        SpinnerOverlay:
            text: root.working
            display: bool(root.working)
'''
)


class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior, RecycleBoxLayout):
    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        """Based on FocusBehavior that provides automatic keyboard
        access, key presses will be used to select children.
        """
        if super().keyboard_on_key_down(window, keycode, text, modifiers):
            return True
        if self.select_with_key_down(window, keycode, text, modifiers):
            return True
        return False

    def keyboard_on_key_up(self, window, keycode):
        """Based on FocusBehavior that provides automatic keyboard
        access, key release will be used to select children.
        """
        if super().keyboard_on_key_up(window, keycode):
            return True
        if self.select_with_key_up(window, keycode):
            return True
        return False


class FileItem(RecycleDataViewBehavior, MDListItem):
    index = NumericProperty()
    icon = StringProperty()
    text = StringProperty()
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)

    def on_touch_down(self, touch):
        # Called by user click on item.
        ret = super().on_touch_down(touch)
        if self.collide_point(*touch.pos):
            return self.parent.select_with_touch(self.index, touch)
        return ret

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super().refresh_view_attrs(rv, index, data)

    def apply_selection(self, rv, index, is_selected):
        self.selected = is_selected


class BackupRestoreCustom(MDBoxLayout):
    instance = None
    increment = None
    is_remote = BooleanProperty()
    error_message = StringProperty()
    error_detail = StringProperty()
    working = StringProperty()
    search = StringProperty()
    file_items = ListProperty()
    # Item selected by the user.
    selected_file = StringProperty(allownone=True)

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
            logger.warning(str(e))
            self.error_message = _('Fail to retrieve available files.')
            self.error_detail = str(e)
        except Exception as e:
            logger.exception('unknown exception')
            self.error_message = _('Unknown problem occured when collecting file list.')
            self.error_detail = str(e)
        finally:
            self.working = ''

    @alias_property(bind=['file_items', 'search'])
    def filtered_files(self):
        if not self.search:
            return self.file_items
        return [item for item in self.file_items if self.search in item['text']]

    def on_search(self, *args):
        # TODO Need to clear the seletected_nodes index
        pass

    def on_selected_file_items(self, widget, nodes):
        """
        Used to select items.
        """
        if not nodes:
            self.selected_file = None
        else:
            idx = nodes[0]
            file_item = widget.recycleview.data[idx]
            self.selected_file = file_item['text']

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
            'BackupRestoreDate', instance=self.instance, increment=self.increment, restore_type='custom'
        )

    def save(self):
        # Prompt user where to restore files/folder.
        async def _save():
            folder = await folder_dialog(parent=self, title=_('Select folder where to restore data'))
            if not folder:
                # Operation cancel by user
                return
            # Trigger restore process of the given file to selected folder.
            self.instance.start_restore(
                restore_time=int(self.increment.timestamp()), paths=self.selected_file, destination=folder
            )
            # Go to Logs
            App.get_running_app().set_active_view('BackupLogs', instance=self.instance)

        self._select_custom_disk_task = asyncio.create_task(_save())
