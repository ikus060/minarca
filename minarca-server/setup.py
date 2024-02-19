#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca Server
#
# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.


import setuptools

setuptools.setup(
    name="minarca_server",
    use_scm_version={"root": "..", "relative_to": __file__},
    description="Minarca Web Server",
    long_description="Minarca is a self-hosted open source data backup software that allows you to manage your computer and server backups for free from a direct online accessible centralized view of your data with easy retrieval in case of displacement, loss or breakage.",
    author="IKUS Software inc.",
    author_email="support@ikus-soft.com",
    maintainer="IKUS Software inc.",
    maintainer_email="support@ikus-soft.com",
    url="https://minarca.org/",
    include_package_data=True,
    python_requires=">=3.5",
    packages=["minarca_server", "minarca_server.plugins", "minarca_server.core", "minarca_server.controller"],
    setup_requires=[
        "setuptools_scm>=3.2,<8",
    ],
    install_requires=[
        "cryptography",
        "cherrypy>=18.0.0",
        "rdiffweb==2.9.0b1",
        "requests",
        "tzlocal~=2.0",
    ],
    # required packages for build process
    extras_require={
        "test": [
            "html5lib",
            "parameterized",
            "pytest",
            "responses",
            "selenium",
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
