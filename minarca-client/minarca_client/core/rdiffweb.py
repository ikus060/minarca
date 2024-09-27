# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Oct. 13, 2023

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''

import requests
from requests.compat import urljoin
from requests.exceptions import ConnectionError

from minarca_client.core import compat
from minarca_client.core.minarcaid import gen_minarcaid_v1


class MinarcaidAuth:
    """
    Custom authentication mecanisme using SSH private key.
    """

    def __init__(self, private_key):
        assert isinstance(private_key, bytes)
        self.private_key = private_key

    def __call__(self, request):
        minarcaid = gen_minarcaid_v1(self.private_key)
        request.headers['Authorization'] = f"Minarcaid {minarcaid}"
        return request


class Rdiffweb:
    def __init__(self, remoteurl):
        assert remoteurl, 'require a remote url'
        self.remoteurl = remoteurl
        # Create HTTP Session using authentication
        self._session = requests.Session()
        self._session.allow_redirects = False
        self._session.headers['User-Agent'] = compat.get_user_agent()

    @property
    def auth(self):
        return self._session.auth

    @auth.setter
    def auth(self, value):
        if isinstance(value, tuple) and len(value) == 2:
            # Basic auth with username / password
            self._session.auth = value
        elif isinstance(value, bytes):
            # Minarcaid ?
            self._session.auth = MinarcaidAuth(value)
        else:
            raise ValueError('invalid auth')

    def _test(self):
        """
        Test connection to remote server.
        """
        # Test URL only once.
        if getattr(self, '_tested', False):
            return
        # Resolve URL Redirection.
        query_url = urljoin(self.remoteurl + '/', '/api/')
        response = self._session.get(query_url, allow_redirects=True)

        if not response.url.endswith('/api/'):
            # If redirection change the path, make it fail.
            raise ConnectionError()
        if query_url != response.url:
            # Session was redirected, query using new location.
            response = self._session.get(response.url)
        response.raise_for_status()
        self.remoteurl = response.url[0:-4]
        self._tested = True

    def post_ssh_key(self, title, public_key):
        self._test()
        response = self._session.post(
            self.remoteurl + 'api/currentuser/sshkeys',
            data={'title': title, 'key': public_key},
        )
        response.raise_for_status()

    def get_current_user_info(self):
        """
        Return current user information.
        """
        self._test()
        response = self._session.get(self.remoteurl + 'api/currentuser/')
        response.raise_for_status()
        return response.json()

    def get_minarca_info(self):
        """
        Return a dict with `version`, `remotehost`, `identity`
        """
        self._test()
        response = self._session.get(self.remoteurl + 'api/minarca/')
        response.raise_for_status()
        return response.json()

    def post_repo_settings(self, id_or_name, maxage=None, keepdays=None, ignore_weekday=None):
        """
        Update repository settings.
        """
        self._test()
        data = {}
        if maxage is not None:
            data['maxage'] = int(maxage)
        if keepdays is not None:
            data['keepdays'] = int(keepdays)
        if isinstance(ignore_weekday, list):
            data['ignore_weekday'] = ignore_weekday
        response = self._session.post(
            f'{self.remoteurl}api/currentuser/repos/{id_or_name}',
            data=data,
        )
        response.raise_for_status()

    def get_repo_settings(self, id_or_name):
        """
        Get the current repository settings.
        """
        self._test()
        response = self._session.get(
            f'{self.remoteurl}api/currentuser/repos/{id_or_name}',
        )
        response.raise_for_status()
        return response.json()
