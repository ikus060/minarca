#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca Server
#
# Copyright (C) 2019 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import print_function

import setuptools

setuptools.setup(
    name="minarca-server",
    use_scm_version={"root": "..", "relative_to": __file__},
    description='Minarca Web Server',
    long_description='Provide Minarca web server to visualize your backup.',
    author='Patrik Dufresne Service Logiciel inc.',
    author_email='support@patrikdufresne.com',
    maintainer='Patrik Dufresne Service Logiciel inc.',
    maintainer_email='support@patrikdufresne.com',
    url='http://www.patrikdufresne.com/en/minarca/',
    include_package_data=True,
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    packages=['minarca_plugins'],
    setup_requires=[
        "setuptools_scm",
    ],
    install_requires=[
        "rdiffweb==1.4.0",
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
        'rdiffweb.IUserQuota': ['MinarcaUserSetup = minarca_plugins:MinarcaUserSetup'],
    },
)
