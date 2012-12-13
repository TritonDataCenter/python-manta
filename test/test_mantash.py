#!/usr/bin/env python
# Copyright (c) 2012 Joyent, Inc.  All rights reserved.

"""Test mantash."""

import os
import sys
import re
from pprint import pprint
import unittest

from testlib import TestError, TestSkipped, tag

from common import *
import manta



#---- globals

TDIR = "tmp/test_mantash"



#---- test cases

class OptionsTestCase(MantaTestCase):
    def test_help(self):
        pass
        ##XXX START HERE
        #code, stdout, stderr = self.mantash(['--help'])
        #self.assertTrue("mantash COMMAND" in stdout)
        #self.assertEqual(stderr, "")
        #self.assertEqual(code, 0)
