#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca Quota API
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import print_function

import setuptools

setuptools.setup(
    name="minarca_quota_api",
    use_scm_version={"root": "..", "relative_to": __file__},
    description='Minarca Quota API',
    long_description='Provide utilities to setup Quota management for rdiffweb / minarca-server.',
    author='IKUS Software inc.',
    url='https://www.ikus-soft.com/en/minarca/',
    packages=['minarca_quota_api'],
    include_package_data=True,
    python_requires='>=3.5',
    setup_requires=[
        "setuptools_scm>=5.0.1",
    ],
    install_requires=[
        'cherrypy',
        'ConfigArgParse'
    ],
    # requirement for testing
    tests_require=[
        "nose",
        "mock>=1.3.0",
        "pytest",
        "coverage",
    ],
    test_suite='nose.collector',
    entry_points={
        "console_scripts": [
            "minarca-quota-api = minarca_quota_api:run"
        ], },
)
