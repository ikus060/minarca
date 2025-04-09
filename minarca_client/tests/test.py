# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
'''
Created on Jun. 14, 2021

@author: Patrik Dufresne <patrik@ikus-soft.com>
'''
import fnmatch


class MATCH(object):
    "A helper object that compares equal using wildcard."

    def __init__(self, pattern):
        self.pattern = pattern

    def __eq__(self, other):
        return fnmatch.fnmatch(other, self.pattern)

    def __ne__(self, other):
        return not fnmatch.fnmatch(other, self.pattern)

    def __repr__(self):
        return '<MATCH %s>' % self.pattern
