#!/usr/bin/env python
# Copyright (c) 2012 Joyent, Inc.  All rights reserved.

"""Test the python-manta."""

import os
import sys
from os.path import join, dirname, abspath, exists, splitext, basename
import re
from pprint import pprint
import unittest
import codecs
try:
    from json import loads as json_loads
except ImportError:
    def json_loads(s):
        # Total hack to get support for 2.4. "simplejson" only supports back
        # to 2.5 now and `json` is only in the Python stdlib >=2.6.
        return eval(s, {}, {})

from testlib import TestError, TestSkipped, tag

import manta



#---- globals

MANTA_URL = os.environ['MANTA_URL']
MANTA_KEY_ID = os.environ['MANTA_KEY_ID']
MANTA_USER = os.environ['MANTA_USER']
INSECURE = False

TDIR = "python-manta-test"



#---- internal support stuff

# Python version compat
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


def stor(*subpaths):
    from posixpath import join as urljoin
    if not subpaths:
        return '/%s/stor' % MANTA_USER
    subpath = urljoin(*subpaths)
    if subpath.startswith("/"):
        subpath = subpath[1:]
    return "/%s/stor/%s" % (MANTA_USER, subpath)

class MantaTestCase(unittest.TestCase):
    _client = None
    def get_client(self):
        if not self._client:
            signer = manta.SSHAgentSigner(key_id=MANTA_KEY_ID)
            self._client = manta.MantaClient(url=MANTA_URL, user=MANTA_USER,
                signer=signer,
                disable_ssl_certificate_validation=INSECURE)
        return self._client



#---- Test cases
#
# We need to run these tests in order. We'll be creating a test area:
#   /$user/stor/python-manta-test/
# and working in there.
#

class MiscTestCase(MantaTestCase):
    """Miscellaneous 'manta' module tests."""
    def test_imports(self):
        self.assertTrue(manta.MantaClient)
        self.assertTrue(manta.PrivateKeySigner)
        self.assertTrue(manta.SSHAgentSigner)
        self.assertTrue(manta.MantaError)
        self.assertTrue(manta.MantaAPIError)

    def test_version(self):
        VERSION_RE = re.compile('^\d+\.\d+\.\d+$')
        self.assertTrue(manta.__version__)
        self.assertTrue(VERSION_RE.search(manta.__version__))

class CleanTestAreaTestCase(MantaTestCase):
    def test_clean(self):
        client = self.get_client()
        #XXX

class DirTestCase(MantaTestCase):
    def test_put(self):
        client = self.get_client()
        client.put_directory(stor(TDIR))
        dirents = client.list_directory(stor())
        dirent = [d for d in dirents if d["name"] == TDIR][0]
        self.assertTrue(dirent)

    def test_list(self):
        client = self.get_client()
        for d in ['a', 'b', 'c']:
            client.put_directory(stor(TDIR, d))
        dirents = client.list_directory(stor(TDIR))
        self.assertEqual(len(dirents), 3)
        dirents = client.list_directory(stor(TDIR), limit=2)
        self.assertEqual(len(dirents), 2)
        dirents = client.list_directory(stor(TDIR), marker=dirents[-1]["name"])
        self.assertEqual(len(dirents), 2)
        self.assertEqual(dirents[1]["name"], "c")

    def test_head(self):
        client = self.get_client()
        for d in ['a', 'b', 'c']:
            client.put_directory(stor(TDIR, d))
        res = client.head_directory(stor(TDIR))
        self.assertEqual(int(res['result-set-size']), 3)

    def test_delete(self):
        client = self.get_client()
        for d in ['a', 'b', 'c']:
            client.delete_directory(stor(TDIR, d))
        dirents = client.list_directory(stor(TDIR))
        self.assertEqual(len(dirents), 0)


class ObjectTestCase(MantaTestCase):
    def test_putgetdel(self):
        client = self.get_client()
        client.put_directory(stor(TDIR))
        mpath = stor(TDIR, 'foo.txt')
        content = 'foo\nbar\nbaz'
        client.put_object(mpath, content=content)
        got = client.get_object(mpath)
        self.assertEqual(content, got)
        client.delete_object(mpath)
        dirents = [e for e in client.list_directory(stor(TDIR))
            if e["name"] == "foo.txt"]
        self.assertEqual(len(dirents), 0)



#---- hook for testlib

def test_cases():
    """This is called by test.py to build up the test cases."""
    yield MiscTestCase
    yield CleanTestAreaTestCase
    yield DirTestCase
    yield ObjectTestCase
