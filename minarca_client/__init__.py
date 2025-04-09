# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
from importlib.metadata import version

try:
    __version__ = version("minarca_client")
except Exception:
    __version__ = "DEV"
