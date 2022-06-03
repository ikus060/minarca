#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca Server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import print_function

import sys

import setuptools

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
    description="Minarca Web Server",
    long_description="Minarca is a self-hosted open source data backup software that allows you to manage your computer and server backups for free from a direct online accessible centralized view of your data with easy retrieval in case of displacement, loss or breakage.",
    author="IKUS Software inc.",
    author_email="support@ikus-soft.com",
    maintainer="IKUS Software inc.",
    maintainer_email="support@ikus-soft.com",
    url="https://www.ikus-soft.com/en/minarca/",
    include_package_data=True,
    python_requires=">=3.5",
    packages=["minarca_server", "minarca_server.plugins"],
    setup_requires=[
        "setuptools_scm>=5.0.1",
    ],
    install_requires=[
        "rdiffweb==2.4.0.a8",
        "cherrypy>=18.0.0",
        "requests",
        "tzlocal~=2.0",
        snakeoil_ver,
    ],
    # required packages for build process
    extras_require={
        "test": [
            "responses",
            "pytest",
        ]
    },
    # Declare entry point
    entry_points={
        "console_scripts": [
            "minarca-server = minarca_server.main:main",
            "minarca-shell = minarca_server.shell:main",
        ]
    },
)
