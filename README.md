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

    # Manta logs at the debug level, so the logging env needs to be setup.
    logging.basicConfig()

    url = os.environ['MANTA_URL']
    user = os.environ['MANTA_USER']
    key_id = os.environ['MANTA_KEY_ID']

    # This handles ssh-key signing of requests to Manta. Manta uses
    # the HTTP Signature scheme for auth.
    # https://github.com/joyent/node-http-signature/blob/master/http_signing.md
    signer = manta.PrivateKeySigner(key_id)

    client = manta.MantaClient(url, user, signer)

    content = client.get('/trent/stor/foo.txt')
    print content


# CLI

TODO: describe mantash


# License

MIT. See LICENSE.txt.




# notes

- `pkgin in py27-crypto-2.4.1` on smartos to get pycrypto
- http://guide.python-distribute.org/pip.html
