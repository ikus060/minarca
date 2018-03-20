#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Minarca disk space plugin
#
# Copyright (C) 2015 Patrik Dufresne Service Logiciel inc. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import print_function

from distutils.cmd import Command
from distutils.command.build import build as build_
import os
import pkg_resources
import setuptools
import subprocess


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


class build_less(Command):
    """
    Command to build less file with lessc.
    """

    description = 'compile *.less files with lessc command.'
    user_options = [
        ('files=', 'f',
         "List of less files to compile. Separated by `;`."),
        ('include-path=', None,
         'Set include paths. Separated by `;`'),
        ('compress', 'x',
         'Compress output by removing some whitespaces.'),
        ('output-dir', None,
         'Output directory where to generate the .less files. Default to current.'),
    ]
    boolean_options = ['compress']

    def initialize_options(self):
        self.files = None
        self.include_path = pkg_resources.resource_filename('rdiffweb', 'static/less')  # @UndefinedVariable
        self.compress = False
        self.output_dir = False

    def finalize_options(self):
        self.files = self.files.split(';')

    def run(self):
        """
        Run `lessc` for each file.
        """
        if not self.files:
            return
        # lessc --include-path=/home/ikus060/workspace/Minarca/rdiffweb.git/rdiffweb/static/less minarca_brand/main.less
        for f in self.files:
            args = ['lessc']
            if self.include_path:
                args.append('--include-path=' + self.include_path)
            if self.compress:
                args.append('--compress')
            # Source
            args.append(f)
            # Destination
            destination = f.replace('.less', '.css')
            if self.output_dir:
                destination = os.path.join(self.output_dir, os.path.basename(destination))
            args.append(destination)
            # Execute command line.
            subprocess.call(args)


class build(build_):
    """
    This is modification of build command, compile_all_catalogs
    is added as last/first command
    """

    sub_commands = build_.sub_commands[:]
    sub_commands.insert(0, ('compile_all_catalogs', None))
    sub_commands.insert(0, ('build_less', None))


setuptools.setup(
    name="minarca-plugins",
    use_scm_version=True,
    description='Minarca Plugins',
    long_description='Sets of plugins for Minarca.',
    author='Patrik Dufresne Service Logiciel inc.',
    url='http://www.patrikdufresne.com/',
    packages=[
        'minarca_brand',
        'minarca_user_setup',
        'minarca_disk_space'
    ],
    include_package_data=True,
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    cmdclass={
        'build': build,
        'compile_all_catalogs': compile_all_catalogs,
        'build_less': build_less,
    },
    install_requires=[
        "rdiffweb>=0.10.5",
        "requests",
    ],
    # required packages for build process
    setup_requires=[
        "babel>=0.9",
        "setuptools_scm",
        # This is required to compile with lessc.
        "rdiffweb>=0.10.5",
    ],
    # requirement for testing
    tests_require=[
        "mock>=1.3.0",
        "mockldap>=0.2.6",
        "pycrypto>=2.6.1",
        "httpretty",
    ],
    # Declare entry point
    entry_points={'rdiffweb.plugins': [
        'MinarcaBrand = minarca_brand',
        'MinarcaDiskSpace = minarca_disk_space',
        'MinarcaUserSetup = minarca_user_setup',
        'MinarcaServerInfo = minarca_server_info',
    ]},
)
