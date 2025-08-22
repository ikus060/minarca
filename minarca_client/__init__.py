# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
from importlib.metadata import version
from importlib.resources import files

try:
    __version__ = version("minarca_client")
except Exception:
    __version__ = "DEV"

# Load branding configuration.
header_name = 'Minarca'
download_url = "https://minarca.org/download/"
link_color = '#1C4062'
navbar_color = '#0E2933'
btn_fg_color = '#FFFFFF'
btn_bg_color = '#009FB9'
try:
    import javaproperties

    config_file = files('minarca_client') / 'minarca.ini'
    config = javaproperties.loads(config_file.read_text())
    header_name = config.get('header-name', header_name)
    download_url = config.get('download-url', download_url)
    link_color = config.get('link-color', link_color)
    navbar_color = config.get('navbar-color', navbar_color)
    btn_fg_color = config.get('btn-fg-color', btn_fg_color)
    btn_bg_color = config.get('btn-bg-color', btn_bg_color)
except Exception:
    # Silently ignore any branding error
    pass
