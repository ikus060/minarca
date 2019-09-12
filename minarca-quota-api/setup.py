#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca Quota API
#
# Copyright (C) 2019 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import print_function

import setuptools

setuptools.setup(
    name="minarca-quota-api",
    use_scm_version={"root": "..", "relative_to": __file__},
    description='Minarca Quota RESTful API',
    long_description='Provide a RESTful API to access and update the the user quota.',
    author='Patrik Dufresne Service Logiciel inc.',
    url='http://www.patrikdufresne.com/',
    packages=['minarca_quota_api'],
    include_package_data=True,
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    setup_requires=[
        "setuptools_scm",
    ],
    install_requires=[
        'cherrypy',
        "future>=0.15.2",
    ],
    # requirement for testing
    tests_require=[
        "mock>=1.3.0",
        "pytest",
        "coverage",
    ],
    entry_points={"console_scripts": ["minarca-quota-api = minarca_quota_api:run"], },
)
