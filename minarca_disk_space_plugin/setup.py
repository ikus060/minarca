#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca disk space plugin
#
# Copyright (C) 2015 Patrik Dufresne Service Logiciel inc. All rights reserved.
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
from distutils.command.build import build as build_
from babel.messages.frontend import compile_catalog
from babel.messages.frontend import extract_messages
from babel.messages.frontend import update_catalog
from babel.messages.frontend import init_catalog
from distutils.cmd import Command
from string import strip


# this is implementation of command which complies all catalogs (dictionaries)
class compile_all_catalogs(Command):
    description = 'compile message catalogs for all languages to binary MO'
    user_options = [
        ('domain=', 'D',
         "domain of PO file (default 'messages')"),
        ('directory=', 'd',
         'path to base directory containing the catalogs'),
        ('locales=', 'l',
         'locale of the catalogs to compile'),
        ('use-fuzzy', 'f',
         'also include fuzzy translations'),
        ('statistics', None,
         'print statistics about translations')
    ]
    boolean_options = ['use-fuzzy', 'statistics']

    def initialize_options(self):
        self.domain = None
        self.directory = None
        self.locales = None
        self.use_fuzzy = False
        self.statistics = False

    def finalize_options(self):
        self.locales = map(strip, self.locales.split(','))

    def run(self):
        for locale in self.locales:
            compiler = compile_catalog(self.distribution)

            compiler.initialize_options()
            compiler.domain = self.domain
            compiler.directory = self.directory
            compiler.locale = locale
            compiler.use_fuzzy = self.use_fuzzy
            compiler.statistics = self.statistics
            compiler.finalize_options()

            compiler.run()


class build(build_):
    """
    This is modification of build command, compile_all_catalogs
    is added as last/first command
    """
    sub_commands = build_.sub_commands[:]
    sub_commands.insert(0, ('compile_all_catalogs', None))

plugin_name = "minarca_disk_space"
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
    install_requires=["rdiffweb>=0.8.2.dev1"],
    # required packages for build process
    setup_requires=["babel>=0.9"]
)
