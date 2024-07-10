# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import datetime
import logging
import os
import shutil
import tempfile

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDListItem

from minarca_client.core import BackupInstance
from minarca_client.core.config import Patterns
from minarca_client.core.exceptions import BackupError
from minarca_client.dialogs import question_dialog
from minarca_client.locale import _
from minarca_client.ui.spinner_overlay import SpinnerOverlay  # noqa
from minarca_client.ui.theme import CButton  # noqa
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)


Builder.load_string(
    '''
<FullRestoreItem>
    divider: True

    MDListItemLeadingIcon:
        icon: root.icon

    MDListItemHeadlineText:
        text: root.comment
        adaptive_height: False
        -height: self.texture_size[1] if root.comment else 0

    MDListItemSupportingText:
        text: root.pattern

    MDListItemTrailingCheckbox:
        active: root.selected
        on_active: root.selected = not root.selected

<BackupRestoreFull>:
    orientation: "horizontal"
    md_bg_color: self.theme_cls.backgroundColor

    SidePanel:
        is_remote: root.is_remote
        restore: True
        text: _("When you perform a full restore, the selected items will be restored to their original location on your device.")

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

            CCard:
                padding: "1dp"

                RecycleView:
                    id: recycleview
                    viewclass: "FullRestoreItem"
                    data: root.file_items

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
                text: _('I understand that full restore replaces existing files on my device and may result in data loss if the destination is not empty.')
                active: root.confirm
                on_active: root.confirm = not root.confirm

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
                    text: _('Restore')
                    on_release: root.save()
                    disabled: root.working or not root.selected_files or not root.confirm

        SpinnerOverlay:
            text: root.working
            display: bool(root.working)
'''
)


class FullRestoreItem(RecycleDataViewBehavior, MDListItem):
    index = NumericProperty()
    icon = StringProperty()
    pattern = StringProperty()
    comment = StringProperty()
    selected = BooleanProperty(False)
    on_selected_item = None

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        return super().refresh_view_attrs(rv, index, data)

    def on_selected(self, *args, **kwargs):
        if self.on_selected_item:
            self.on_selected_item(self.index, self)


class BackupRestoreFull(MDBoxLayout):
    instance = None
    increment = None
    is_remote = BooleanProperty()
    error_message = StringProperty()
    error_detail = StringProperty()
    working = StringProperty()
    file_items = ListProperty()
    confirm = BooleanProperty(False)

    _fetch_filters_task = None

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
        self._fetch_filters_task = asyncio.create_task(self._fetch_filters(instance))

    async def _fetch_filters(self, instance):
        # TODO Warn against full restore when operating system is different
        try:
            # Fetch previous filter from backup
            temp_dir = tempfile.mkdtemp()
            await instance.restore(
                restore_time=str(int(self.increment.timestamp())), paths=[instance.patterns_file], destination=temp_dir
            )
            # Load previous patterns file
            file_items = []
            fn = os.path.join(temp_dir, os.path.basename(instance.patterns_file))
            patterns = Patterns(fn)
            for pattern in patterns:
                if not pattern.include:
                    # Ignore exclude patterns
                    continue
                file_items.append(
                    {
                        'comment': pattern.comment or "",
                        'pattern': pattern.pattern,
                        'icon': 'file-outline',
                        'selected': False,
                        'on_selected_item': self.on_selected_item,
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
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._fetch_filters_task:
            self._fetch_filters_task.cancel()

    @alias_property(bind=['file_items'])
    def selected_files(self):
        return [item['pattern'] for item in self.file_items if item['selected']]

    def on_selected_item(self, index, item):
        if index < 0 or index >= len(self.file_items):
            return
        # Update list of selected
        self.file_items[index]['selected'] = not self.file_items[index]['selected']
        # Trigger update
        self.property('file_items').dispatch(self)

    def cancel(self):
        # Go back to dashboard
        App.get_running_app().set_active_view(
            'BackupRestoreDate', instance=self.instance, increment=self.increment, restore_type='full'
        )

    def save(self):
        # Prompt user where to restore files/folder.
        async def _save():
            ret = await question_dialog(
                parent=self,
                title=_('Confirm Full Restore'),
                message=_('Are you sure you want to run a full restoration?'),
                detail=_(
                    'This action will overwrite all existing files selected with the previous version present in the backup. This action is irreversible and may result in data loss.'
                ),
            )
            if not ret:
                # Operation cancel by user
                return
            # Trigger restore process of the given file to selected folder.
            self.instance.start_restore(restore_time=int(self.increment.timestamp()), paths=self.selected_files)
            # Go to Logs
            App.get_running_app().set_active_view('BackupLogs', instance=self.instance)

        self._select_custom_location_task = asyncio.create_task(_save())
