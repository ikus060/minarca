# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 25, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import os
import tkinter

import pkg_resources
from minarca_client.core.compat import IS_MAC, IS_WINDOWS

# Reference to application icons.
if IS_WINDOWS:
    MINARCA_ICON = pkg_resources.resource_filename(__name__, 'images/minarca.ico')
elif IS_MAC:
    MINARCA_ICON = pkg_resources.resource_filename(__name__, 'images/minarca.icns')
else:
    MINARCA_ICON = pkg_resources.resource_filename(__name__, 'images/minarca_128.png')

