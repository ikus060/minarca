# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import re
import sys
from importlib import resources
from pathlib import Path

from .config import KeyValueConfigFile

branding_root = Path(sys.executable).parent
branding_fn = branding_root / 'minarca.cfg'


def _css_color(value):
    """Validate CSS Color"""
    # Validate the color code.
    if not re.match('^#?(?:[0-9a-fA-F]{3}){1,2}$', value):
        raise ValueError("invalid CSS Color")
    if value.startswith('#'):
        return value
    return '#' + value


def _file(value):
    """Coerse string into Path only if file exists."""
    p = branding_root / value
    if not p.is_file():
        print('FOO: %s' % p)
        raise ValueError('not a file')
    return p


class AppConfig(KeyValueConfigFile):
    _fields = [
        ('header_name', str, 'Minarca'),
        ('download_url', str, 'https://minarca.org/download/'),
        ('link_color', _css_color, '#1C4062'),
        ('navbar_color', _css_color, '#0E2933'),
        ('btn_fg_color', _css_color, '#FFFFFF'),
        ('btn_bg_color', _css_color, '#009FB9'),
        ('favicon', _file, resources.files('minarca_client') / 'ui/theme/resources/favicon.png'),
        ('header_logo', _file, resources.files('minarca_client') / 'ui/theme/resources/header-logo-32.png'),
    ]


appconfig = AppConfig(branding_fn)
