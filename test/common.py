#!/usr/bin/env python
# Copyright (c) 2012 Joyent, Inc.  All rights reserved.

"""Shared code for test case files."""

__all__ = ["stor", "MantaTestCase"]

import sys
import os
from posixpath import join as ujoin
from pprint import pprint
import unittest
import subprocess

import manta



#---- globals

MANTA_URL = os.environ['MANTA_URL']
MANTA_KEY_ID = os.environ['MANTA_KEY_ID']
MANTA_USER = os.environ['MANTA_USER']
MANTA_INSECURE = bool(os.environ.get('MANTA_INSECURE', False))



#---- internal support stuff

def stor(*subpaths):
    if not subpaths:
        return '/%s/stor' % MANTA_USER
    subpath = ujoin(*subpaths)
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
                disable_ssl_certificate_validation=MANTA_INSECURE)
        return self._client

    def mantash(self, args):
        mantash = os.path.realpath(
            os.path.join(os.path.dirname(__file__), "..", "bin", "mantash"))
        argv = [sys.executable, mantash] + args
        XXX # START HERE
