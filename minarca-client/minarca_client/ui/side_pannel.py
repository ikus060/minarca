# Copyleft (C) 2023 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import logging

from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, StringProperty
from kivymd.uix.boxlayout import MDBoxLayout

from minarca_client.locale import _

logger = logging.getLogger(__name__)

Builder.load_string(
    '''
<SidePanel>:
    orientation: "vertical"
    md_bg_color: self.theme_cls.surfaceContainerColor
    size_hint: (None, 1)
    width: "390dp"
    padding: "50dp"
    spacing: "20dp"

    CLabel:
        text: root._title
        font_style: "Title"
        role: "large"
        halign: "center"
        pos_hint: {"top": 1}

    CLabel:
        text: root.text
        halign: "center"

    Image:
        source: root._icon
        fit_mode: "contain"
        pos_hint: {"center_x": .5, "center_y": .5}

    CBoxLayout:
        pos_hint: {"center_x": .5}
        size_hint: (None, None)
        height: "20dp"
        width:  "80dp"
        display: root.create

        CLabel:
            text: "\u2022"
            theme_font_size: "Custom"
            font_size: "60dp"
            text_color: self.theme_cls.primaryColor if root.step == 1 else self.theme_cls.onSurfaceColor

        CLabel:
            text: "\u2022"
            theme_font_size: "Custom"
            font_size: "60dp"
            text_color: self.theme_cls.primaryColor if root.step == 2 else self.theme_cls.onSurfaceColor

        CLabel:
            text: "\u2022"
            theme_font_size: "Custom"
            font_size: "60dp"
            text_color: self.theme_cls.primaryColor if root.step == 3 else self.theme_cls.onSurfaceColor
'''
)


class SidePanel(MDBoxLayout):
    is_remote = BooleanProperty(False)
    create = BooleanProperty(False)
    restore = BooleanProperty(False)
    text = StringProperty("")
    step = NumericProperty(0)
    maximum = NumericProperty(0)

    # Update automatically.
    _title = StringProperty("")
    _icon = StringProperty("")

    def __init__(self, *args, **kwargs):
        super(MDBoxLayout, self).__init__(*args, **kwargs)
        self._title = self.get_title()
        self._icon = self.get_icon()

    def on_is_remote(self, *args, **kwargs):
        self._title = self.get_title()
        self._icon = self.get_icon()

    def on_create(self, *args, **kwargs):
        self._title = self.get_title()

    def on_restore(self, *args, **kwargs):
        self._title = self.get_title()

    def get_title(self):
        if self.is_remote:
            if self.create:
                return _('Create an online backup')
            elif self.restore:
                return _('Online restore')
            else:
                return _('Online backup')
        else:
            if self.create:
                return _('Create a local backup')
            elif self.restore:
                return _('Local restore')
            else:
                return _('Local backup')

    def get_icon(self):
        if self.is_remote:
            return "remote-backup-256.png"
        else:
            return "local-backup-256.png"
