import asyncio
import datetime

from kivy.lang import Builder
from kivy.properties import DictProperty
from kivymd.app import MDApp

from minarca_client.ui.date_picker import CDatePicker  # noqa
from minarca_client.ui.tests import BaseAppTest


class DemoDateSelectionApp(MDApp):
    selectable_dates = DictProperty(
        {
            datetime.date(2023, 12, 20): 1,
            datetime.date(2024, 1, 22): 1,
            datetime.date(2024, 2, 26): 1,
            datetime.date(2024, 3, 27): 1,
        }
    )

    def _clear_widgets_recursive(self, widget):
        # Do nothing. This is implementedin MinarcaApp.
        pass

    def build(self):
        return Builder.load_string(
            """
MDScreen:
    md_bg_color: self.theme_cls.backgroundColor

    MDBoxLayout:
        orientation: "vertical"

        CDatePicker:
            id: date_picker
            selectable_dates: app.selectable_dates

        MDLabel:
            text: "This is a Demo of DateSelection Widget"
            disabled: True

        MDLabel:
            text: "This is a Demo of DateSelection Widget"
            disabled: False
"""
        )


class DateSelectionTest(BaseAppTest):
    async def asyncSetUp(self):
        self.app = DemoDateSelectionApp()
        self._task = asyncio.create_task(self.app.async_run())
        await self.pump_events()
        self.assertIsNotNone(self.app.root)

    async def test_view(self):
        # Given a date picker
        date_picker = self.app.root.ids.date_picker
        # Given a displayed date
        date_picker.year = 2024
        date_picker.month = 3
        date_picker.day = 28
        # Given a selected date
        date_picker.sel_year = 2024
        date_picker.sel_month = 3
        date_picker.sel_day = 27

        # When user click on crevron
        date_picker.ids.month_selection_items.ids.chevron_left.dispatch('on_release')
        # Then displayed date get updated
        await asyncio.sleep(1)
        self.assertEqual(date_picker.month, 2)

        # When user click on crevron
        date_picker.ids.month_selection_items.ids.chevron_right.dispatch('on_release')
        # Then displayed date get updated
        await asyncio.sleep(1)
        self.assertEqual(date_picker.month, 3)

        # When user click on crevron
        date_picker.ids.year_selection_items.ids.chevron_left.dispatch('on_release')
        # Then displayed date get updated
        await asyncio.sleep(1)
        self.assertEqual(date_picker.year, 2023)

        # When user click on crevron
        date_picker.ids.year_selection_items.ids.chevron_right.dispatch('on_release')
        # Then displayed date get updated
        await asyncio.sleep(1)
        self.assertEqual(date_picker.year, 2024)


if __name__ == "__main__":
    DemoDateSelectionApp().run()
