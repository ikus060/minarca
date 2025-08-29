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
        raise ValueError('not a file')
    return p


def _str(value):
    """Check if valid string"""
    if not isinstance(value, str):
        raise TypeError('required a string')
    if len(value) <= 0:
        raise ValueError('empty string')
    if len(value) > 255:
        raise ValueError('too long')
    return value


def _url(value):
    """Check if valid URL."""
    if not value.startswith('http://') and not value.startswith('https://'):
        raise ValueError('invalid url scheme')
    return value


class AppConfig(KeyValueConfigFile):
    _fields = [
        ('header_name', _str, 'Minarca'),
        ('download_url', _url, 'https://minarca.org/download/'),
        ('remote_url', _url, ''),
        ('link_color', _css_color, '#1C4062'),
        ('navbar_color', _css_color, '#0E2933'),
        ('btn_fg_color', _css_color, '#FFFFFF'),
        ('btn_bg_color', _css_color, '#009FB9'),
        ('favicon', _file, resources.files('minarca_client') / 'ui/theme/resources/favicon.png'),
        ('header_logo', _file, resources.files('minarca_client') / 'ui/theme/resources/header-logo-32.png'),
    ]


appconfig = AppConfig(branding_fn)
