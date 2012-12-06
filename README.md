A Python client and 'mantash' CLI and shell for Joyent Manta.


# Installation

Eventually (when python-manta is published to PyPI) this:

    pip install manta

Until then:

    make package  # TODO
    pip install path/to/python-manta-VERSION.tgz  # TODO


# Setup

First setup your environment to match your Joyent Manta account:

    $ export MANTA_KEY_ID=`ssh-keygen -l -f ~/.ssh/id_rsa.pub | awk '{print $2}' | tr -d '\n'`
    $ export MANTA_URL=https://manta.us-east.joyentcloud.com
    $ export MANTA_USER=trent


# Python Usage

    import os
    import logging
    import manta

    # Manta logs at the trace level, so the logging env needs to be setup.
    logging.basicConfig()

    url = os.environ['MANTA_URL']
    key_id = os.environ['MANTA_KEY_ID']   # TODO this being a sig *or* a pubkey path
    user = os.environ['MANTA_USER']

    # This handle ssh-key signing of requests to Manta. Manta uses
    # HTTP-Signature for auth
    # https://github.com/joyent/node-http-signature/blob/master/http_signing.md
    signer = manta.PrivateKeySigner(user=user, key_id=key_id)

    client = manta.MantaClient(user=user, url=url, key_id=key_id, sign=signer)

    content = client.get('/trent/stor/foo.txt')
    print content


# CLI

TODO: describe mantash


# notes

- http://guide.python-distribute.org/pip.html
