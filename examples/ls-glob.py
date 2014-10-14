#!/usr/bin/env python

"""A small example showing how to do a globbing `ls` if a directory in Manta
using the python-manta client.

At the time of this writing the python MantaClient does not support glob
handling. For an involved example see the "do_ls" method in "bin/mantash"
for glob handling.

Usage:
    python ls-glob.py [-v] <manta-path-with-file-glob>

Example:
    $ python ls-glob.py /trent.mick/stor/tmp/*.m4a
    /trent.mick/stor/tmp/blue.m4a
    /trent.mick/stor/tmp/excursion.m4a

Use '-v' option for verbose output.
"""

import logging
import os
from pprint import pprint
import sys
import posixpath
from fnmatch import fnmatch

# Import the local manta module.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import manta


def get_client(verbose=False):
    MANTA_USER = os.environ['MANTA_USER']
    MANTA_URL = os.environ['MANTA_URL']
    MANTA_TLS_INSECURE = bool(os.environ.get('MANTA_TLS_INSECURE', False))
    MANTA_NO_AUTH = os.environ.get('MANTA_NO_AUTH', 'false') == 'true'
    if MANTA_NO_AUTH:
        signer = None
    else:
        MANTA_KEY_ID = os.environ['MANTA_KEY_ID']
        signer = manta.CLISigner(key_id=MANTA_KEY_ID)
    client = manta.MantaClient(url=MANTA_URL,
        account=MANTA_USER,
        signer=signer,
        verbose=verbose,
        disable_ssl_certificate_validation=MANTA_TLS_INSECURE)
    return client


#---- mainline

logging.basicConfig()
if '-v' in sys.argv:
    sys.argv.remove('-v')
    verbose = True
else:
    verbose = False

client = get_client(verbose)
if len(sys.argv) < 2:
    sys.stderr.write('ls-glob.py error: not enough arguments\n\n')
    sys.stderr.write('usage: python ls-glob.py <manta-path-with-file-glob>\n')
    sys.exit(1)
mpath = sys.argv[1]

# Naively presuming the last element is a *file* glob.
mdir, mbase = posixpath.split(mpath)
d = client.list_directory(mdir)

# Use `fnmatch` to locally filter based on the given glob pattern.
# Note that this doesn't support globs in the dirs leading up to the base
# filename.
for dirent in d:
    if fnmatch(dirent["name"], mbase):
        print posixpath.join(mdir, dirent["name"])
