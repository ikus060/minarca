# Define kivy configuration manually
import os

from kivy.config import Config  # noqa

try:
    from importlib.resources import resource_filename
except ImportError:
    # For Python 2 or Python 3 with older setuptools
    from pkg_resources import resource_filename

# Disable exit on ESC key press
Config.set('kivy', 'exit_on_escape', 0)

# Disable right click
Config.set('input', 'mouse', 'mouse,disable_multitouch')

# Define default application icons
minarca_ico = resource_filename('minarca_client', 'ui/theme/resources/minarca.ico')
if os.path.isfile(minarca_ico):
    Config.set('kivy', 'window_icon', minarca_ico)

# Define default size
Config.set('graphics', 'height', '768')
Config.set('graphics', 'width', '1024')
