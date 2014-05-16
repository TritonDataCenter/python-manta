#!/usr/bin/env python

"""A small example showing how to mkdir in
Manta using the python-manta client.
"""

import os
from pprint import pprint
import sys

# Import the local manta module.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import manta


def get_client():
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
        # Uncomment this for verbose client output for test run.
        #verbose=True,
        disable_ssl_certificate_validation=MANTA_TLS_INSECURE)
    return client


#---- mainline

client = get_client()

# First, there is the base `RawMantaClient` that just provides a light wrapper
# around the Manta REST API (http://apidocs.joyent.com/manta/api.html).
# For example, the `put_directory` method corresponds to the PutDirectory
# endpoint (http://apidocs.joyent.com/manta/api.html#PutDirectory).
mpath = '/%s/public/hello-raw' % os.environ['MANTA_USER']
print('# RawMantaClient.put_directory(%r)' % mpath)
client.put_directory(mpath)

# Then there are some convenience methods on the `MantaClient` subclass. For
# example the `mkdir` method takes an optional `parents=True` to do the
# equivalent of `mkdir -p`.
mpath = '/%s/public/hello/there/manta' % os.environ['MANTA_USER']
print('# MantaClient.mkdir(%r)' % mpath)
client.mkdir(mpath, parents=True)
