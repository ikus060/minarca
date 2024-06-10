# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
try:
    from importlib.metadata import distribution as get_distribution
except ImportError:
    # For Python 2 or Python 3 with older setuptools
    from pkg_resources import get_distribution

try:
    __version__ = get_distribution("minarca_client").version
except Exception:
    __version__ = "DEV"
