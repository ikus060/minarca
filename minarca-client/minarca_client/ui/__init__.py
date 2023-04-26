# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import pkg_resources
import tkvue

from minarca_client.locale import gettext

# Configure translation
tkvue.gettext = gettext

# Configure TK with our theme.
theme_file = pkg_resources.resource_filename("minarca_client.ui", "theme/minarca.tcl")
tkvue.configure_tk(
    basename="Minarca",
    classname="Minarca",
    # Put best resolution first for MacOS.
    # Provide 16px for Windows
    icon=["minarca-256", "minarca-128", "minarca-32", "minarca-16"],
    theme="minarca",
    theme_source=theme_file,
)
