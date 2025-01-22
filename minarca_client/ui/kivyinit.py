# Define kivy configuration manually

from importlib.resources import files

from kivy.core.window import Window

# Set background to white
Window.clearcolor = (1, 1, 1, 1)

from kivy.config import Config  # noqa

# Disable exit on ESC key press
Config.set('kivy', 'exit_on_escape', 0)

# Disable right click
Config.set('input', 'mouse', 'mouse,disable_multitouch')

# Define default application icons
minarca_ico_path = files('minarca_client') / 'ui/theme/resources/minarca.ico'
if minarca_ico_path.is_file():
    Config.set('kivy', 'window_icon', str(minarca_ico_path))

# Define default size to fit on small screen (1360x768)
Config.set('graphics', 'height', '675')
Config.set('graphics', 'width', '1024')
