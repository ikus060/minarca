#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca disk space plugin
#
# Copyright (C) 2015 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import print_function

import sys
PY2 = sys.version_info[0] == 2

# Check running python version.
if not PY2 and not sys.version_info >= (3, 4):
    print('python version 3.4 is required.')
    sys.exit(1)

if PY2 and not sys.version_info >= (2, 7):
    print('python version 2.7 is required.')
    sys.exit(1)

import os
from distutils.cmd import Command
from distutils.command.build import build as build_
from distutils.dist import DistributionMetadata
from distutils.log import error, info
from distutils.util import split_quoted
from string import Template

try:
    from ConfigParser import SafeConfigParser
except ImportError:
    from configparser import SafeConfigParser

try:
    from setuptools import setup
except ImportError:
    import ez_setup
    ez_setup.use_setuptools()
    from setuptools import setup

DistributionMetadata.templates = None


class fill_template(Command):
    """
    Custom distutils command to fill text templates with release meta data.
    """

    description = "Fill placeholders in documentation text file templates"

    user_options = [
        ('templates=', None, "Template text files to fill")
    ]

    def initialize_options(self):
        self.templates = ''
        self.template_ext = '.in'

    def finalize_options(self):
        if isinstance(self.templates, str):
            self.templates = split_quoted(self.templates)

        self.templates += getattr(self.distribution.metadata, 'templates', None) or []

        for tmpl in self.templates:
            if not tmpl.endswith(self.template_ext):
                raise ValueError(
                    "Template file '%s' does not have expected " +
                    "extension '%s'." % (tmpl, self.template_ext))

    def run(self):
        metadata = self.get_metadata()

        for infilename in self.templates:
            try:
                info("Reading template '%s'...", infilename)
                with open(infilename) as infile:
                    tmpl = Template(infile.read())
                    outfilename = infilename.rstrip(self.template_ext)

                    info("Writing filled template to '%s'.", outfilename)
                    with open(outfilename, 'w') as outfile:
                        outfile.write(tmpl.safe_substitute(metadata))
            except:
                error("Could not open template '%s'.", infilename)

    def get_metadata(self):
        data = dict()
        for attr in self.distribution.metadata.__dict__:
            if not callable(attr):
                data[attr] = getattr(self.distribution.metadata, attr)

        return data


class compile_all_catalogs(Command):
    """
    This is implementation of command which complies all catalogs
    (dictionaries).
    """

    description = 'compile message catalogs for all languages to binary MO files'
    user_options = [
        ('domains=', 'D',
         "domains of PO file (default 'messages')"),
        ('directories=', 'd',
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
        self.domains = None
        self.directories = None
        self.locales = None
        self.use_fuzzy = False
        self.statistics = False

    def finalize_options(self):
        self.locales = list(map(str.strip, self.locales.split(',')))
        self.domains = list(map(str.strip, self.domains.split(',')))
        self.directories = list(map(str.strip, self.directories.split(',')))

    def run(self):
        from babel.messages.frontend import compile_catalog

        def compile(domain, directory):
            for locale in self.locales:
                compiler = compile_catalog(self.distribution)
                compiler.initialize_options()
                compiler.domain = domain
                compiler.directory = directory
                compiler.locale = locale
                compiler.use_fuzzy = self.use_fuzzy
                compiler.statistics = self.statistics
                compiler.finalize_options()
                compiler.run()

        list(map(compile, self.domains, self.directories))


class build(build_):
    """
    This is modification of build command, compile_all_catalogs
    is added as last/first command
    """

    sub_commands = build_.sub_commands[:]
    sub_commands.insert(0, ('compile_all_catalogs', None))
    sub_commands.insert(0, ('filltmpl', None))

# Read package info from yapsy plugin file.
# config = SafeConfigParser()
# config.read(plugin_file)

# Create recursive data_files
# dest = "/etc/rdiffweb/plugins"
# datadir = plugin_name
# data_files = [
#    (os.path.join(dest, root), [os.path.join(root, f) for f in files])
#    for root, dirs, files in os.walk(datadir)]
# data_files.append((dest, [plugin_file]))

setup(
    name="minarca-plugins",
    version='0.9.1',
    description='Minarca Plugins',
    long_description='Sets of plugins for Minarca.',
    author='Patrik Dufresne Service Logiciel inc.',
    url='http://www.patrikdufresne.com/',
    packages=[
        'minarca_brand',
        'minarca_user_setup',
        'minarca_disk_space'
    ],
    cmdclass={
        'build': build,
        'compile_all_catalogs': compile_all_catalogs,
        'filltmpl': fill_template,
    },
    templates=['sonar-project.properties.in'],
    install_requires=["rdiffweb>=0.9"],
    # required packages for build process
    setup_requires=[
        "babel>=0.9",
    ],
    # requirement for testing
    tests_require=[
        "mockldap>=0.2.6",
    ]
)
