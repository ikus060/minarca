# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 25, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
from tkinter import ttk

import pkg_resources
from minarca_client.core.compat import IS_MAC, IS_WINDOWS

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

# Location of minarca theme.
themes_file = pkg_resources.resource_filename('minarca_client.ui', 'templates/themes.json')
assert themes_file


def style(master):
    s = ttk.Style(master=master)
    s.theme_use('clam')
    for i in ['primary', 'secondary', 'success', 'info', 'warning', 'danger']:
        s.configure('H1.%s.TLabel' % i, font=["Helvetica", "36"])
        s.configure('small.%s.TLabel' % i, font=["Helvetica", "10"])
        s.configure('strong.%s.TLabel' % i, font=["Helvetica", "14", "bold"])
    s.configure('Tooltip.TLabel', background="#ffffe0")
