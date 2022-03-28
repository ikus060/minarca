# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
from pkg_resources import DistributionNotFound

try:
    import pkg_resources

    __version__ = pkg_resources.get_distribution("minarca_client").version
except DistributionNotFound:
    __version__ = "DEV"
