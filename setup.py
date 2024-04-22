#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca client
#
# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.


import setuptools

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
        "setuptools_scm>=3.2,<8",
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
    install_requires=[
        "aiofiles",
        "cryptography",
        "humanfriendly",
        "javaproperties",
        "packaging",
        "psutil",
        "rdiff-backup==2.2.5",
        "requests>=2.25.1",
        "tzlocal~=2.0",
        "wakepy==0.6.0",
        "kivy==2.3.0",
        # TODO We need to define version
        "KivyMD @ git+https://github.com/kivymd/KivyMD@cfe5aac30f50708c6208c8b33b0ef1aa390721e8",
        # Windows dependencies
        "pywin32 ; sys_platform=='win32'",
        # MacOS dependencies
        "launchd ; sys_platform=='darwin'",
        # TODO We need to define version when release. This is required to compile on MacOS.
        "materialyoucolor @ git+https://github.com/T-Dynamos/materialyoucolor-python.git@57ec2e45ea4596edae0d9133af4732fa25a6407e ; sys_platform=='darwin'",
        # Linux dependencies
        "python-crontab ; sys_platform=='linux'",
        "pylibacl ; sys_platform=='linux'",
        "pyxattr ; sys_platform=='linux'",
    ],
)
