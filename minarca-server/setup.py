#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca Server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import print_function

import setuptools

setuptools.setup(
    name="minarca-server",
    use_scm_version={"root": "..", "relative_to": __file__},
    description='Minarca Web Server',
    long_description='Minarca is a self-hosted open source data backup software that allows you to manage your computer and server backups for free from a direct online accessible centralized view of your data with easy retrieval in case of displacement, loss or breakage.',
    author='IKUS Software inc.',
    author_email='support@ikus-soft.com',
    maintainer='IKUS Software inc.',
    maintainer_email='support@ikus-soft.com',
    url='https://www.ikus-soft.com/en/minarca/',
    include_package_data=True,
    python_requires='>=3.5',
    packages=['minarca_plugins'],
    setup_requires=[
        "setuptools_scm",
    ],
    install_requires=[
        "rdiffweb==2.0.3a6",
        "cherrypy>=16.0.0",
        "requests",
    ],
    # required packages for build process
    tests_require=[
        "mock>=1.3.0",
        "mockldap>=0.2.6",
        "httpretty",
        "pytest",
    ],
    # Declare entry point
    entry_points={
        'rdiffweb.IUserChangeListener': ['MinarcaUserSetup = minarca_plugins:MinarcaUserSetup'],
        'rdiffweb.IUserQuota': ['MinarcaUserSetup = minarca_plugins:MinarcaQuota'],
        "console_scripts": ["minarca-shell = minarca_plugins.shell:main"]
    },
)
