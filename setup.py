#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca client
#
# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import print_function

import os
import sys

import setuptools

install_requires = [
    "javaproperties",
    "packaging",
    "psutil",
    "rdiff-backup==2.2.5",
    "requests>=2.25.1",
    "tkvue==2.1.4",
    "wakepy==0.6.0",
]

if os.name == "nt":
    extra_options = {
        "install_requires": install_requires + ["pywin32"],
        # On Windows rdiff-backup is not working with python 3.9
        # Let make it a required until rdiff-backup support other python
        # version.
        "python_requires": ">=3.10, <3.11",
    }

elif sys.platform == "darwin":
    extra_options = {
        # On MacOS, we use launchd for scheduling
        "install_requires": install_requires + ["launchd"],
        # Python 3.6 and more are supported
        "python_requires": "~=3.7",
    }

else:
    extra_options = {
        # On Linux we use Crontab for scheduling
        "install_requires": install_requires + ["python-crontab", "pylibacl", "pyxattr"],
        # Python 3.6 and more are supported
        "python_requires": "~=3.7",
    }

setuptools.setup(
    name="minarca_client",
    use_scm_version={"root": "..", "relative_to": __file__},
    description="Opensource software to backup all your data.",
    long_description="Minarca is a self-hosted open source data backup software that allows you to manage your computer and server backups for free from a direct online accessible centralized view of your data with easy retrieval in case of displacement, loss or breakage.",
    author="IKUS Software inc.",
    author_email="support@ikus-soft.com",
    maintainer="IKUS Software inc.",
    maintainer_email="support@ikus-soft.com",
    url="https://minarca.org/",
    include_package_data=True,
    packages=setuptools.find_packages("."),
    setup_requires=[
        "setuptools_scm>=3.2",
    ],
    # required packages for build process
    extras_require={
        "test": [
            "parameterized",
            "responses",
        ]
    },
    # Declare an entry point when package get installed using pip.
    entry_points={
        "console_scripts": ["minarca = minarca_client.main:main"],
        "gui_scripts": ["minarcaw = minarca_client.main:main"],
    },
    **extra_options
)
