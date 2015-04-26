#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca brand plugin
#
# Copyright (c) 2015 Patrik Dufresne Service Logiciel All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

try:
    from setuptools import setup, find_packages, Extension
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup, find_packages, Extension  # @UnusedImport

import os
from ConfigParser import SafeConfigParser


plugin_name = "minarca_brand"
plugin_file = plugin_name + '.plugin'

# Read package info from yapsy plugin file.
config = SafeConfigParser()
config.read(plugin_file)

# Create recursive data_files
dest = "/etc/rdiffweb/plugins"
datadir = plugin_name
data_files = [
    (os.path.join(dest, root), [os.path.join(root, f) for f in files])
    for root, dirs, files in os.walk(datadir)]
data_files.append((dest, [plugin_file]))

setup(
    name=plugin_name,
    version=config.get("Documentation", "Version"),
    description=config.get("Core", "Name"),
    long_description=config.get("Documentation", "Description"),
    author=config.get("Documentation", "Author"),
    url=config.get("Documentation", "Website"),
    data_files=data_files,
    cmdclass={
        'build': build,
        'compile_catalog': compile_catalog,
        'extract_messages': extract_messages,
        'update_catalog': update_catalog,
        'init_catalog': init_catalog,
        'compile_all_catalogs': compile_all_catalogs,
        },
    install_requires=["rdiffweb>=0.8.0"],
    # required packages for build process
    setup_requires=["babel>=0.9"]
    )
