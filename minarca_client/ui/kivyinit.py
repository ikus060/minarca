# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

# Define kivy configuration manually
import sys

from kivy.config import Config  # noqa

from minarca_client.core.appconfig import appconfig

# Disable exit on ESC key press
Config.set('kivy', 'exit_on_escape', 0)

# Disable right click
Config.set('input', 'mouse', 'mouse,disable_multitouch')

# Disable /dev/mtdev lookup on Linux
if sys.platform == 'linux':
    Config.set('input', '%(name)s', '')

# Define default application icons
Config.set('kivy', 'window_icon', str(appconfig.favicon))

# Define default size to fit on small screen (1360x768)
Config.set('graphics', 'height', '675')
Config.set('graphics', 'width', '1024')
