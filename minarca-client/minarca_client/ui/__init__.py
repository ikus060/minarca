# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
import pkg_resources
from minarca_client.ui import tkvue

# Configure TK with our theme.
theme_file = pkg_resources.resource_filename('minarca_client.ui', 'theme/minarca.tcl')
tkvue.configure_tk(
    basename='Minarca',
    classname='Minarca',
    icon=['minarca-16', 'minarca-32', 'minarca-128'],
    theme='minarca',
    theme_source=theme_file)
