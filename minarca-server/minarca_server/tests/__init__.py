# -*- coding: utf-8 -*-
#
# Minarca server
#
# Copyright (C) 2020 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

import os
import pwd
import shutil
import tempfile
import unittest

import rdiffweb
import rdiffweb.test

from minarca_server.app import MinarcaApplication


class AbstractMinarcaTest(rdiffweb.test.WebCase):
    """
    Abstract test class to setup minarca for testing.
    """

    app_class = MinarcaApplication

    @classmethod
    def setup_class(cls):
        if cls is AbstractMinarcaTest:
            raise unittest.SkipTest("%s is an abstract base class" % cls.__name__)
        cls.base_dir = tempfile.mkdtemp(prefix='minarca_tests_')
        if not os.path.isdir(cls.base_dir):
            os.mkdir(cls.base_dir)
        # Use temporary folder for base dir
        cls.default_config['MinarcaUserBaseDir'] = cls.base_dir
        cls.default_config['logfile'] = os.path.join(cls.base_dir, 'server.log')
        # Use current user for owner and group
        cls.default_config['MinarcaUserDirOwner'] = pwd.getpwuid(os.getuid())[0]
        cls.default_config['MinarcaUserDirGroup'] = pwd.getpwuid(os.getuid())[0]
        super(AbstractMinarcaTest, cls).setup_class()

    @classmethod
    def teardown_class(cls):
        super(AbstractMinarcaTest, cls).teardown_class()
        shutil.rmtree(cls.base_dir, ignore_errors=True)
