# Copyright (C) 2025 IKUS Software. All right reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import os

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
size = (1024, 675)
density = os.environ.get('KIVY_METRICS_DENSITY', '1')
try:
    density = float(density)
    size = [int(x * density) for x in size]
except ValueError:
    pass  # ignore invalid density value
Config.set('graphics', 'width', str(size[0]))
Config.set('graphics', 'height', str(size[1]))
