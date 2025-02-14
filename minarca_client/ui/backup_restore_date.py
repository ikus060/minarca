# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import asyncio
import datetime
import logging

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout

from minarca_client.core import BackupInstance
from minarca_client.core.exceptions import BackupError
from minarca_client.locale import _
from minarca_client.ui.date_picker import CDatePicker  # noqa
from minarca_client.ui.spinner_overlay import SpinnerOverlay  # noqa
from minarca_client.ui.theme import CButton
from minarca_client.ui.utils import alias_property

logger = logging.getLogger(__name__)

# TODO For Remote backup, invite user to restore online.

Builder.load_string(
    '''
<IncrementItem>:
    group: "restore_date"
    theme_bg_color: "Custom"
    md_bg_color: self.theme_cls.primaryColor if root.selected else self.theme_cls.surfaceContainerHighColor
    theme_text_color: "Custom"
    text_color: self.theme_cls.onPrimaryColor if root.selected else self.theme_cls.onSurfaceColor
    -size_hint_x: None
    theme_width: "Custom"
    width: "120dp"
    text: root.inc.strftime("%X") if root.inc else ""

    MDButtonIcon:
        theme_icon_color: "Custom"
        icon_color: self.theme_cls.onPrimaryColor if root.selected else self.theme_cls.onSurfaceColor
        icon: "restore"

<BackupRestoreDate>:
    orientation: "horizontal"
    md_bg_color: self.theme_cls.backgroundColor

    SidePanel:
        is_remote: root.is_remote
        restore: True
        text: _("Choose the point in time of data to be restored.")

    MDRelativeLayout:

        MDBoxLayout:
            orientation: "vertical"
            padding: "50dp"
            spacing: "15dp"
            pos_hint: {'top': 1}

            CLabel:
                text: _("Select date & Time")
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

            MDBoxLayout:
                orientation: 'horizontal'
                spacing: "20dp"
                adaptive_height: True

                CDatePicker:
                    id: date_picker
                    selectable_dates: root.selectable_dates
                    on_select_day: root.on_select_day(self.sel_year, self.sel_month, self.sel_day)

                RecycleView:
                    viewclass: "IncrementItem"
                    data: root.increment_items
                    do_scroll_x: False

                    RecycleBoxLayout:
                        spacing: "5dp"
                        padding: "0dp"
                        default_size: None, "40dp"
                        default_size_hint: 1, None
                        orientation: 'vertical'
                        size_hint: None, None
                        width: "120dp"
                        height: self.minimum_height

            Widget:

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
                    text: _('Next')
                    on_release: root.save()
                    disabled: root.working or root.selected_increment is None

        SpinnerOverlay:
            text: root.working
            display: bool(root.working)

'''
)


class IncrementItem(CButton):
    inc = ObjectProperty()
    selected = BooleanProperty()
    on_select_increment_item = None

    def on_release(self):
        if self.on_select_increment_item:
            self.on_select_increment_item(self)


class BackupRestoreDate(MDBoxLayout):
    instance = None
    is_remote = BooleanProperty()
    error_message = StringProperty()
    error_detail = StringProperty()
    working = StringProperty()
    increments = ListProperty()
    selected_date = ObjectProperty(allow_none=True)
    selected_increment = ObjectProperty(allow_none=True)

    _fetch_increment_task = None

    def __init__(self, backup=None, instance=None, increment=None):
        assert backup
        assert instance and isinstance(instance, BackupInstance)
        assert increment is None or isinstance(increment, datetime.datetime)
        # Initialise the state.
        self.instance = instance
        self.is_remote = self.instance.is_remote()
        self.selected_increment = increment
        # Create the view
        super().__init__()
        # Sync calendar with selected day & selected increment.
        date_picker = self.ids.date_picker
        if self.selected_increment:
            date_picker.sel_year = increment.year
            date_picker.sel_month = increment.month
            date_picker.sel_day = increment.day
        self.selected_date = datetime.date(date_picker.sel_year, date_picker.sel_month, date_picker.sel_day)

        # Start task to get increments list.
        self.working = _('Please wait. Loading backup dates...')
        self._fetch_increment_task = asyncio.create_task(self._fetch_increments(instance))

    async def _fetch_increments(self, instance):
        try:
            self.increments = await instance.list_increments()
        except BackupError as e:
            logger.warning(str(e))
            self.error_message = _('Failed to retrieve available backup dates.')
            self.error_detail = str(e)
        except Exception as e:
            logger.exception('unknown exception')
            self.error_message = _('Unknown problem occurred when collecting backup dates.')
            self.error_detail = str(e)
        finally:
            self.working = ''

    def on_parent(self, widget, value):
        if value is None:
            self._cancel_tasks()

    def _cancel_tasks(self, event=None):
        """On destroy, make sure to delete task."""
        if self._fetch_increment_task:
            self._fetch_increment_task.cancel()

    def on_select_day(self, year, month, day):
        """
        Trigger when user click a new date in calendar.
        """
        if year and month and day:
            self.selected_date = datetime.date(year, month, day)
        else:
            self.selected_date = None

    def on_select_increment_item(self, item):
        """
        Trigger when user click an increment.
        """
        if item and item.inc:
            self.selected_increment = item.inc

    @alias_property(bind=['increments'])
    def selectable_dates(self):
        # Return the date portion of increments.
        return {inc.date(): None for inc in self.increments}

    @alias_property(bind=['increments', 'selected_date', 'selected_increment'])
    def increment_items(self):
        # Return list of items to be displayed
        if not self.selected_date:
            return []
        return [
            {
                'inc': inc,
                'selected': inc == self.selected_increment,
                "on_select_increment_item": self.on_select_increment_item,
            }
            for inc in self.increments
            if inc.date() == self.selected_date
        ]

    def cancel(self):
        # Go back to dashboard
        App.get_running_app().set_active_view('dashboard.DashboardView')

    def save(self):
        if not self.selected_increment:
            # Should never get here.
            return
        # Next step, select files
        App.get_running_app().set_active_view(
            'backup_restore_files.BackupRestoreFiles',
            instance=self.instance,
            increment=self.selected_increment,
        )
