# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from kivy.lang import Builder
from kivy.properties import StringProperty

from minarca_client.ui.theme import CBoxLayout

Builder.load_string(
    '''
<SpinnerOverlay>:
    orientation: "vertical"
    size_hint: 1, 1
    md_bg_color: [1, 1, 1, 0.6]
    spacing: "30dp"
    pos_hint: {'center_x': .5, 'center_y': .5}

    Widget:
        size_hint_y: 0.5

    CSpinner:
        size_hint: None, None
        size: "60dp", "60dp"
        pos_hint: {'center_x': .5, 'center_y': .5}

    CLabel:
        text: root.text
        halign: "center"
        pos_hint: {'center_x': .5, 'center_y': .5}

    Widget:
'''
)


class SpinnerOverlay(CBoxLayout):
    text = StringProperty()
