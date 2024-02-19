import os
import sys

# On Windows, to avoid OpenGL 1.1. error. Force angle_sdl2
if sys.platform in ['win32'] and 'KIVY_GL_BACKEND' not in os.environ:
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
# Disable Kivy config file.
os.environ['KIVY_NO_CONFIG'] = "1"
# Configure kivy logging
os.environ['KIVY_NO_FILELOG'] = "1"
os.environ['KIVY_LOG_MODE'] = "PYTHON"
