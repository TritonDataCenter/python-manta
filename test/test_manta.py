#!/usr/bin/env python
# Copyright (c) 2012 Joyent, Inc.  All rights reserved.

"""Test the python-manta."""

import os
import sys
from os.path import join, dirname, abspath, exists, splitext, basename
import re
from glob import glob
from pprint import pprint
import unittest
import codecs
import difflib
import doctest
try:
    from json import loads as json_loads
except ImportError:
    def json_loads(s):
        # Total hack to get support for 2.4. "simplejson" only supports back
        # to 2.5 now and `json` is only in the Python stdlib >=2.6.
        return eval(s, {}, {})

from testlib import TestError, TestSkipped, tag

import manta



#---- Python version compat

# Use `bytes` for byte strings and `unicode` for unicode strings (str in Py3).
if sys.version_info[0] <= 2:
    py3 = False
    try:
        bytes
    except NameError:
        bytes = str
    base_string_type = basestring
elif sys.version_info[0] >= 3:
    py3 = True
    unicode = str
    base_string_type = str
    unichr = chr



#---- Test cases

class MiscTestCase(unittest.TestCase):
    """Miscellaneous 'manta' module tests."""

    def test_imports(self):
        self.assertTrue(manta.MantaClient)
        self.assertTrue(manta.PrivateKeySigner)



#---- internal support stuff


#---- hook for testlib

def test_cases():
    """This is called by test.py to build up the test cases."""
    yield MiscTestCase
    #yield GetTestCase
