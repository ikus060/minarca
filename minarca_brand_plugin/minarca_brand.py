#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Minarca disk space rdiffweb plugin
#
# Copyright (C) 2015 Patrik Dufresne Service Logiciel. All rights reserved.
# Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.

from __future__ import unicode_literals

import logging
import os

from rdiffweb.rdw_plugin import IRdiffwebPlugin

class MinarcaBrand(IRdiffwebPlugin):
    """
    This plugin update the configuration to use a different header name and
    logo.
    """
