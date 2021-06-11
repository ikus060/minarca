# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 25, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from minarca_client.core.compat import IS_WINDOWS, IS_MAC
import PySimpleGUI as sg  # @UnresolvedImport
import pkg_resources

# Define the TTK theme to be used
# See https://tkdocs.com/tutorial/styles.html
if IS_WINDOWS:
    TTK_THEME = 'winnative'  # vista, winnative or winxpnative
elif IS_MAC:
    TTK_THEME = 'clam'  # aqua theme cannot be used otherwise it break the look
else:
    TTK_THEME = 'clam'

# Reference to application icons.
if IS_WINDOWS:
    MINARCA_ICON = pkg_resources.resource_filename(__name__, 'images/minarca.ico')
elif IS_MAC:
    MINARCA_ICON = pkg_resources.resource_filename(__name__, 'images/minarca.icns')
else:
    MINARCA_ICON = pkg_resources.resource_filename(__name__, 'images/minarca_128.png')

# On Mac OS X the DPI is not the same. The font size must be bigger
if IS_MAC:
    BASE_FONT_SIZE = 19  # 14 x 96/72
else:
    BASE_FONT_SIZE = 14

#
# Default styles
#
TEXT_DANGER = {'text_color': '#DF382C'}
TEXT_DEFAULT = {'font': ('TkTextFont', BASE_FONT_SIZE)}
TEXT_HEADER1 = {'font': ('TkTextFont', int(BASE_FONT_SIZE * 2.14), 'bold'), 'text_color': '#1c4c72'}
TEXT_SMALL = {'font': ('Lato', int(BASE_FONT_SIZE * 0.72))}
TEXT_STRONG = {'font': ('Lato', BASE_FONT_SIZE, 'bold')}
TEXT_SUCCESS = {'text_color': '#88a944'}
TEXT_SUCCESS = {'text_color': '#88a944'}
TEXT_WARNING = {'text_color': '#f57900'}

BUTTON_LINK = {
    'button_color': ("#1c4c72", "#ffffff"),
    'mouseover_colors': ('#DF382C', '#ffffff'),
    'pad': (1, 1),
    'border_width': 0,
    'font': ('Lato', BASE_FONT_SIZE, 'underline')}
BUTTON_LIST = {
    'size': (22, 1),
    'button_color': ("#787878", "#ebebeb"),
    'pad': (1, 1),
    'border_width': 0}
BUTTON_SUCCESS = {
    'button_color': ("#fefefe", "#88a944"),
    'border_width': 0}

theme = {
    "BACKGROUND": "#ffffff",
    "TEXT": "#464545",
    "INPUT": "#ffffff",
    "TEXT_INPUT": "#222222",
    "SCROLL": "#a5a4a4",
    "BUTTON": ("#fefefe", "#1c4c72"),
    "PROGRESS": sg.DEFAULT_PROGRESS_BAR_COMPUTE,
    "BORDER": 0,
    "SLIDER_DEPTH": 0,
    "PROGRESS_DEPTH": 0,
    "ACCENT1": "#ff5414",
    "ACCENT2": "#33a8ff",
    "ACCENT3": "#dbf0ff",
}
sg.theme_add_new('minarca', theme)
sg.theme('minarca')


def pull_right(layout):
    """
    Used to pull right an element.
    """
    if not isinstance(layout, list):
        layout = [[layout]]
    return sg.Column(
        layout,
        pad=(0, 0),
        expand_x=True,
        element_justification='right')
