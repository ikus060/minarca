# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
from pkg_resources import DistributionNotFound

try:
    import pkg_resources

    __version__ = pkg_resources.get_distribution("minarca_client").version
except DistributionNotFound:
    __version__ = "DEV"
