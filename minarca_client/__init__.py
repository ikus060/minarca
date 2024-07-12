# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
from importlib.metadata import distribution as get_distribution

try:
    __version__ = get_distribution("minarca_client").version
except Exception:
    __version__ = "DEV"
