# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import kivy.utils
from kivymd.font_definitions import theme_font_styles

# Need to replace font definition.
kivy.utils.hex_colormap['minarca'] = "#009FB9"
theme_font_styles["Title"] = {
    "large": {
        "line-height": 1.28,
        "font-name": "Roboto",
        "font-size": "20sp",
    },
    "medium": {
        "line-height": 1.24,
        "font-name": "Roboto",
        "font-size": "18sp",
    },
    "small": {
        "line-height": 1.20,
        "font-name": "Roboto",
        "font-size": "16sp",
    },
}

import os

import kivy.resources
from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ColorProperty, DictProperty, ObjectProperty, OptionProperty, StringProperty
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex
from kivymd.theming import ThemeManager
from kivymd.uix.behaviors import BackgroundColorBehavior, DeclarativeBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button.button import MDButton
from kivymd.uix.label.label import MDLabel
from kivymd.uix.list import MDListItem
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.progressindicator.progressindicator import MDCircularProgressIndicator
from kivymd.uix.selectioncontrol.selectioncontrol import MDSwitch
from kivymd.uix.textfield.textfield import MDTextField

resources_path = os.path.abspath(os.path.join(__file__, '../resources'))
kivy.resources.resource_add_path(resources_path)

# https://fonts.google.com/specimen/Overpass+Mono
LabelBase.register(name='monospace', fn_regular='OverpassMono-VariableFont_wght.ttf')

Builder.load_string(
    '''
#:import _ minarca_client.locale._
<CCard>:
    padding: dp(30)
    style: "outlined"
    theme_bg_color: "Custom"
    md_bg_color: self.theme_cls.backgroundColor
    radius: "0dp"
    canvas.after:
        Color:
            rgba: self.theme_cls.surfaceContainerHighColor
        Line:
            rectangle: [self.x, self.y, self.width, self.height]
            width: 1

<CLabel>:
    size_hint_y: None
    height: self.texture_size[1]
    role: "medium"

<CButton>:
    radius: "0dp"
    style: "filled"
    md_bg_color_disabled: [1,1,1, 0.7]
    text_padding: dp(0) if self.style == 'text' else {'small': dp(15), 'medium': dp(22), 'large': dp(22)}.get(root.role)
    -height: {'small': "30dp", 'medium': "40dp", 'large': "50dp"}.get(root.role)
    canvas.after:
        Color:
            rgba: 1,1,1,1 if self.focus else 0
        Line:
            dash_length: 5
            dash_offset: 2
            rectangle: [self.x + 2, self.y + 2, self.width - 4, self.height - 4]
            width: 1

    MDButtonText:
        theme_text_color: root.theme_text_color
        text_color: root.text_color
        text: root.text
        role: root.role
        font_style: "Body"

<CTextField>:
    mode: "outlined"
    radius: "0dp"
    write_tab: False
    multiline: False

    MDTextFieldHintText:
        text: root.name
        text_color_normal: self.theme_cls.onSurfaceColor

<CSpinner>:
    color: self.theme_cls.primaryColor

<MDSwitch>:
    ripple_effect: False
    #track_color_active: self.theme_cls.primaryColor

<CListItem>:
    -spacing: "10dp"
    -padding: "10dp", "13dp", "10dp", "11dp"
    -height: "40dp"

<CDropDown>:
    write_tab: False
    multiline: False
    readonly: True
    on_focus: self.open()

    MDTextFieldHintText:
        text: root.name

    MDTextFieldTrailingIcon:
        icon: "chevron-down"

<CCheckbox>:
    orientation: 'horizontal'
    spacing: "10dp"
    adaptive_height: True

    MDCheckbox:
        id: checkbox
        active: root.active
        on_active: root.active = self.active
        pos_hint: {'center_y': .5}

    MDLabel:
        text: root.text
        adaptive_height: True
        # When user click on label, toggle the state.
        on_touch_down:
            if self.collide_point(*args[1].pos) and not root.disabled: \
            root.ids.checkbox.active = not root.ids.checkbox.active

<CScrollView>:
    bar_width: 10
    scroll_type: ['bars', 'content']

'''
)


class MinarcaTheme(ThemeManager):
    """
    Custom implementation of theme manager to have better control over the colors generated.
    """

    warningColor = ColorProperty()
    warningContainerColor = ColorProperty()
    onWarningColor = ColorProperty()

    _primary = get_color_from_hex("#009FB9")
    _dark = get_color_from_hex("#0E2933")
    _white = get_color_from_hex("#ffffff")
    _gray_10 = get_color_from_hex("#EEF0F1")
    _gray_20 = get_color_from_hex("#CFD4D6")
    _gray_50 = get_color_from_hex("#7E8D92")
    _danger = get_color_from_hex("#CA393C")
    _secondary = get_color_from_hex("#B6DDE2")
    _secondary_50 = get_color_from_hex("#DBEEF0")
    _warning = get_color_from_hex("#D88C46")
    _warning_20 = get_color_from_hex("#FFF0D9")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dynamic_scheme_name = "TONAL_SPOT"
        self.primary_palette = 'Minarca'
        self.theme_style_switch_animation = False

    def set_colors(self, *args) -> None:
        super().set_colors(*args)
        # Enforce some default colors on top of the scheme.
        self.primaryColor = self._primary
        self.backgroundColor = self._white
        self.errorColor = self._danger
        self.surfaceColor = self._white
        self.onSurfaceColor = self._dark
        self.secondaryColor = self._secondary
        self.onSecondaryColor = self._dark
        self.surfaceContainerColor = self._gray_10
        self.surfaceContainerHighColor = self._gray_20
        self.onSurfaceVariantColor = self._dark
        self.inverseSurfaceColor = self._dark
        self.inverseOnSurfaceColor = self._white
        # Custom color name
        self.warningColor = self._warning
        self.warningContainerColor = self._warning_20
        self.onWarningColor = self._dark


class BaseDisplay(Widget):
    display = BooleanProperty(True)
    _parent = None
    _prev = None

    def on_parent(self, widget, value):
        # Keep reference to previous parent.
        if value:
            self._parent = value

    def on_display(self, widget, value):
        # If we don't have any parent. We don't have anything to do.
        if self._parent is None:
            return
        # Let remove/add Widget.
        if value and widget.parent is None:
            self.show_widget()
        elif not value and widget.parent is not None:
            self.hide_widget()

    def show_widget(self):
        assert self._parent
        _shadow = getattr(self._parent, '_shadow', {})
        idx = _shadow.get(self, 0)
        self._parent.add_widget(self, index=idx)

    def hide_widget(self):
        assert self._parent
        _shadow = getattr(self._parent, '_shadow', None)
        if _shadow is None:
            _shadow = self._parent._shadow = {}
        idx = self._parent.children.index(self)
        _shadow[self] = idx
        self._parent.remove_widget(self)


class CCard(MDBoxLayout):
    pass


class CLabel(MDLabel, BaseDisplay):
    pass


class CButton(MDButton, BaseDisplay, FocusBehavior):
    """
    Custom button with additional support for focus behavior.
    """

    text = StringProperty("change me")
    theme_text_color = OptionProperty(
        "Primary",
        options=[
            "Primary",
            "Secondary",
            "Hint",
            "Error",
            "Custom",
        ],
    )
    text_color = ColorProperty([1, 1, 1, 1])
    role = OptionProperty("medium", options=["large", "medium", "small"])

    def keyboard_on_key_up(self, window, keycode):
        if keycode[1] in ['spacebar', 'enter']:
            self.dispatch('on_release')
        return super().keyboard_on_key_up(window, keycode)


class CTextField(MDTextField):
    name = StringProperty("change me")


class CSpinner(MDCircularProgressIndicator, BaseDisplay):
    pass


class CSwitch(MDSwitch):
    pass


class CListItem(MDListItem):
    pass


class CDropDown(MDTextField):
    """
    Custom implementation of Dropdown menu.
    """

    name = StringProperty("Change Me")
    data = DictProperty()
    value = ObjectProperty()
    _drop_item_menu: MDDropdownMenu = None

    def open(self):
        # When losing focus do nothing.
        if not self.focus:
            return
        # If menu was created, re-open
        if self._drop_item_menu:
            self._drop_item_menu.dismiss()
        # Create Menu using data
        menu_items = [
            {
                "text": label,
                "on_release": lambda key=key: self._menu_callback(key),
            }
            for key, label in self.data.items()
        ]
        self._drop_item_menu = MDDropdownMenu(caller=self, items=menu_items, position="bottom")
        self._drop_item_menu.open()

    def on_value(self, widget, value):
        # Lookup data for corresponding label.
        label = self.data.get(value) or ""
        self.text = label

    def on_data(self, widget, value):
        # When data is getting updated, we may need to update the text value.
        label = self.data.get(self.value) or ""
        self.text = label

    def _menu_callback(self, key):
        # Assign new value
        self.value = key
        # Close menu
        self._drop_item_menu.dismiss()
        self._drop_item_menu = None


class CCheckbox(MDBoxLayout, BaseDisplay):
    """
    Custom implementation of Dropdown menu.
    """

    text = StringProperty("Change Me")
    active = BooleanProperty()


class CBoxLayout(MDBoxLayout, BaseDisplay):
    pass


class CScrollView(DeclarativeBehavior, BackgroundColorBehavior, ScrollView):
    pass
