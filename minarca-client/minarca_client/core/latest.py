# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Oct. 22, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import requests
from packaging import version

from minarca_client.core import compat
from minarca_client.locale import _

LATEST_VERSION_URL = 'https://latest.ikus-soft.com/minarca/latest_version'


class LatestCheckFailed(Exception):
    pass


class LatestCheck:
    """
    Responsible to check if current version is up-to-date.
    """

    def get_download_url(self):
        """
        Return Minarca download page.
        """
        return _("https://minarca.org/download/")

    def get_latest_version(self, timeout=0.5):
        """
        Query the latest version of minarca.
        """
        try:
            # Replace User agent by something meaningful.
            headers = {
                'User-Agent': compat.get_user_agent(),
            }
            # Query data
            response = requests.get(LATEST_VERSION_URL, headers=headers, timeout=timeout)
            # Check status
            response.raise_for_status()
            # Parse data as json
            return response.text
        except requests.exceptions.RequestException as e:
            raise LatestCheckFailed(e)

    def get_current_version(self):
        import minarca_client

        return minarca_client.__version__

    def is_latest(self):
        """
        Check if the current minarca client is up to date.
        """
        # Get current version.
        current_version = self.get_current_version()
        if current_version == 'DEV':
            return True
        try:
            current_version = version.Version(current_version)
        except version.InvalidVersion:
            raise LatestCheckFailed('invalid current_version: ' + current_version)

        # Get latest version
        latest_version = self.get_latest_version()
        try:
            latest_version = version.Version(latest_version)
        except version.InvalidVersion:
            raise LatestCheckFailed('invalid latest_version: ' + latest_version)

        # Compare them
        return current_version >= latest_version
