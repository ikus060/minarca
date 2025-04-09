# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import datetime
import os
from itertools import zip_longest

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import DictProperty, ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.pickers.datepicker.datepicker import MDBaseDatePicker

NO_DISPLAY = not os.environ.get('DISPLAY', False)

Builder.load_string(
    """
<CDatePickerBaseSelectionContainer>
    size_hint: None, None
    size: self.minimum_size

    MDIconButton:
        id: chevron_left
        icon: "chevron-left"
        on_release: root.dispatch("on_release", "prev")

    MDLabel:
        id: label
        adaptive_size: True
        text: root.text
        pos_hint: {"center_y": .5}
        padding: 0
        font_style: "Label"
        role: "large"
        halign: "center"

    MDIconButton:
        id: chevron_right
        icon: "chevron-right"
        on_release: root.dispatch("on_release", "next")

<CDatePicker>:
    calendar_layout: calendar_layout
    size_hint: None, None
    size: calendar_layout.width - self.padding[0] / 2, self.minimum_height
    orientation: "vertical"
    padding: 0, 0, 0, "12dp"

    BoxLayout:
        id: month_year_selection_items_container
        size_hint_y: None
        height: self.minimum_height
        padding: "12dp"

        CDatePickerMonthSelectionItem:
            id: month_selection_items
            text: root._current_month_name
            date_picker: root

        Widget:

        CDatePickerYearSelectionItem:
            id: year_selection_items
            text: str(root.year)
            date_picker: root

    RelativeLayout:
        size_hint: None, None
        size: calendar_layout.size

        MDCalendarLayout:
            id: calendar_layout
            padding: dp(12), 0, dp(12), 0
"""
)


class CDatePickerBaseSelectionContainer(BoxLayout):
    """
    Base class to swithc Year and Month.
    """

    text = StringProperty()
    date_picker = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_release")

    def on_release(self, *args) -> None:
        """
        Fired when the 'chevron-left' or 'chevron-right' buttons are pressed.
        """
        pass


class CDatePickerYearSelectionItem(CDatePickerBaseSelectionContainer):
    def on_release(self, direction: str) -> None:
        """
        Fired when the 'chevron-left' or 'chevron-right' buttons are pressed.
        """

        def set_year(*args):
            self.date_picker.update_calendar(year, self.date_picker.month)
            self.date_picker.restore_calendar_layout_properties()

        year = self.date_picker.year
        if direction == "prev":
            year -= 1
        elif direction == "next":
            year += 1

        if year < self.date_picker.min_year or year > self.date_picker.max_year:
            # Do nothing if year is out of range.
            return

        self.date_picker.set_calendar_layout_properties(set_year)


class CDatePickerMonthSelectionItem(CDatePickerBaseSelectionContainer):
    def on_release(self, direction: str) -> None:
        """
        Fired when the 'chevron-left' or 'chevron-right' buttons are pressed.
        """

        def set_month(*args):
            self.date_picker.change_month(direction)
            self.date_picker._update_date_label_text()
            self.date_picker.restore_calendar_layout_properties()

        self.date_picker.set_calendar_layout_properties(set_month)


class CDatePicker(MDBaseDatePicker):
    selectable_dates = DictProperty()

    def __init__(self, year=None, month=None, day=None, firstweekday=6, **kwargs):
        self.bind(selectable_dates=self._on_selectable_dates)
        super().__init__(year, month, day, firstweekday, **kwargs)
        # Force visibility of the calendar.
        self.opacity = 1
        if not self.ids:
            # Depending of initialization, widget might not be initialized, so trigger another call after.
            Clock.schedule_once(lambda dt: self.generate_list_widgets_days(), 0.51)
            Clock.schedule_once(lambda dt: self.update_calendar(self.sel_year, self.sel_month), 0.52)

    def _on_selectable_dates(self, instance, value):
        # When list of selectable dates get updated, make sure to update the min/max dates values
        if self.selectable_dates:
            self.min_date = min(self.selectable_dates)
            self.max_date = max(self.selectable_dates)
            self.min_year = self.min_date.year
            self.max_year = self.max_date.year
        # TODO If selected date not selectable, pick latest date.
        if self._calendar_list:
            # Update calendar only if calandar items were created.
            self.update_calendar(self.sel_year, self.sel_month)

    def generate_list_widgets_days(self) -> None:
        if self.parent is None or not self.ids:
            # When called in __init__ widgets are not yet initialized.
            return
        super().generate_list_widgets_days()

    def update_calendar(self, year, month) -> None:
        if self.parent is None or not self.ids:
            # When called in __init__ widgets are not yet initialized.
            return
        super().update_calendar(year, month)
        dates = self.calendar.itermonthdates(year, month)
        for widget, widget_date in zip_longest(self._calendar_list, dates):
            # Check if date is selectable.
            widget.disabled = widget_date not in self.selectable_dates
            # Remove "is_in_range" feature
            widget.is_in_range = False

    def _update_date_label_text(self):
        # Replace default implementation by showing the current date
        self._current_month_name = datetime.date(self.year, self.month, self.day).strftime("%b").capitalize()
        # Also make sure to update the chevrons states.
        self.ids.year_selection_items.ids.chevron_left.disabled = self.year <= self.min_year
        self.ids.year_selection_items.ids.chevron_right.disabled = self.year >= self.max_year
        self.ids.month_selection_items.ids.chevron_left.disabled = (self.year, self.month) <= (
            (self.min_date.year, self.min_date.month) if self.min_date else (self.min_year, 1)
        )
        self.ids.month_selection_items.ids.chevron_right.disabled = (self.year, self.month) >= (
            (self.max_date.year, self.max_date.month) if self.max_date else (self.max_year, 12)
        )

    def dismiss(self, *args) -> None:
        # Do nothing - This implentation of Date Picker is not dismissable
        pass

    def open(self) -> None:
        # Do nothing - Should never be call.
        pass
