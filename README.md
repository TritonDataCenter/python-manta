A Python client and 'mantash' CLI and shell for Joyent Manta.


# Installation

For developers:

    git clone git@github.com:joyent/python-manta.git
    export PATH=`pwd`/python-manta/bin:$PATH

The 'pycrypto' (aka 'Crypto') Python module is a binary dependency. Python
module installation is a bit of a gong show, in general, but here are some
things to try:

    # Mac (using system python)
    sudo easy_install pycrypto

    # SmartOS
    pkgin in py27-crypto-2.4.1` on smartos to get pycrypto

    # Any platform using ActivePython
    pypm install pycrypto

    # Other
    # Please let me know what works for you so I can add instructions to the
    # list here.

Eventually (when packaging and releases are implemented) this:

    pip install path/to/python-manta-VERSION.tgz  # not yet implemented (TODO)

Eventually (when python-manta is published to PyPI) this:

    pip install manta    # not yet working (TODO)




# Setup

First setup your environment to match your Joyent Manta account:

    $ export MANTA_KEY_ID=`ssh-keygen -l -f ~/.ssh/id_rsa.pub | awk '{print $2}' | tr -d '\n'`
    $ export MANTA_URL=https://manta-beta.joyentcloud.com
    $ export MANTA_USER=trentm


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

    content = client.get_object('/trent/stor/foo.txt')
    print content


# CLI

TODO: describe mantash


# License

MIT. See LICENSE.txt.

Some pure Python dependencies are included in this distribution (to
reduce install dependency headaches). They are covered by their
respective licenses:

- paramiko (http://www.lag.net/paramiko/): LGPL
- httplib2 (http://code.google.com/p/httplib2/): MIT
- cmdln (https://github.com/trentm/cmdln): MIT
- appdirs (https://github.com/ActiveState/appdirs): MIT


# Limitations

The python-manta Python API isn't currently well-suited to huge objects
or huge directory listings (>10k dirents) because responses are fully
buffered in memory rather than being streamed. If streaming is a requirement
for your use case, you could consider the [Manta Node.js
bindings](https://github.com/joyent/node-manta).

For other limitations (also planned work) see TODO.txt.


# notes

- `pkgin in py27-crypto-2.4.1` on smartos to get pycrypto
- http://guide.python-distribute.org/pip.html
