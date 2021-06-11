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
import sys

# snakeoil package drop support for py35, py36, and py37
PY_VERSION = (sys.version_info.major, sys.version_info.minor)
snakeoil_ver = "snakeoil"
if PY_VERSION < (3, 8):
    snakeoil_ver = "snakeoil<0.9.0"
if PY_VERSION < (3, 6):
    snakeoil_ver = "snakeoil<0.8.0"

setuptools.setup(
    name="minarca_server",
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
        "setuptools_scm>=5.0.1",
    ],
    install_requires=[
        "rdiffweb==2.3.2.dev7+g9d9d7e4",
        "cherrypy>=16.0.0",
        "requests",
        "tzlocal",
        snakeoil_ver,
    ],
    # required packages for build process
    tests_require=[
        "nose",
        "mock>=1.3.0",
        "mockldap>=0.2.6",
        "httpretty",
        "pytest",
    ],
    test_suite='nose.collector',
    # Declare entry point
    entry_points={
        'rdiffweb.IUserChangeListener': ['MinarcaUserSetup = minarca_plugins:MinarcaUserSetup'],
        'rdiffweb.IUserQuota': ['MinarcaUserSetup = minarca_plugins:MinarcaQuota'],
        "console_scripts": ["minarca-shell = minarca_plugins.shell:main"]
    },
)
