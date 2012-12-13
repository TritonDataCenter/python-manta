A Python SDK for Manta (Joyent's Object Store and Cloud Compute system).
This provides a Python 'manta' package and a 'mantash' (Manta Shell) CLI
and shell.


# Current Status

Beta stability. Still under active development. Tested mostly on Mac and
SmartOS using Python 2.6 or 2.7.

The *intention* is to support Windows (if reasonable) and Linux; and Python
>=2.5 and Python 3 (again, if reasonable). Supporting Python 3 might largely
depend on python-manta's dependencies (paramiko and pycrypto).

Please send all feedback to Trent Mick on the <manta-private-beta@joyent.com>.


# Installation

## pycrypto dependency

The 'pycrypto' (aka 'Crypto') Python module is a binary dependency. If you
use SmartOS and Python 2.7, then the Crypto module is included already and
you don't need a separate install.

Python module installation is a bit of a gong show, in general, but here are
some things to try:

    # Mac (using system python)
    sudo easy_install pycrypto

    # SmartOS
    # - `pkgin in py27-crypto-2.4.1` is insufficient (DATASET-627)
    # - a binary build for SunOS/Python-2.7 is included
    **Please let me know if this binary build fails for you, e.g. dependency
    issue or different Python version.**

    # Any platform using the ActivePython distribution of Python
    pypm install pycrypto

    # Other
    # Please let me know what works for you so I can add instructions to the
    # list here. Often one of the following will do it:
    easy_install pycrypto
    pip install pycrypto


## python-manta

    wget https://manta-beta.joyentcloud.com/trentm/public/python-manta/python-manta-latest.tgz
    tar xzf python-manta-latest.tgz
    cd python-manta-*   # the actual directory is 'python-manta-VERSION'
    export PATH=$PATH:`pwd`/bin


## verify it works

The 'mantash' CLI should now work:

    $ mantash help
    ...

For Python usage you need to get the 'lib' directory on your Python Path.
One way is:

    export PYTHONPATH=`pwd`/lib



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
    signer = manta.SSHAgentSigner(key_id)

    client = manta.MantaClient(url, user, signer)

    content = client.get_object('/trent/stor/foo.txt')
    print content

    print dir(client)   # list all methods, better documentation coming (TODO)


# CLI

This package also provides a `mantash` (MANTA SHell) CLI for working with
Manta:

    $ mantash help
    Usage:
        mantash COMMAND [ARGS...]
        mantash help [COMMAND]
    ...
    Commands:
        cat            print objects
        cd             change directory
        find           find paths
        get            get a file from manta
        job            Run a Manta job
    ...

    # This is a local file.
    $ ls
    numbers.txt

    # Mantash single commands can be run like:
    #       mantash ls
    # Or you can enter the mantash interactive shell and run commands from
    # there. Let's do that:
    $ mantash
    [https://manta-beta.joyentcloud.com/trent/stor]$ ls
    [.../trent/stor]$                       # our stor is empty for now
    [.../trent/stor]$ put numbers.txt ./    # upload local file
    [.../trent/stor]$ ls
    numbers.txt
    [.../trent/stor]$ cat numbers.txt
    one
    two
    three
    four

    # List available commands. A number of the typical Unix-y commands are
    # there.
    [.../trent/stor]$ help
    ...

    # Manta jobs.
    #
    # Note: The '^' is used as an alternative pipe separator to '|'.
    # The primary reason is to avoid Bash eating the pipe when running
    # one-off `mantash job ...` commands in Bash.

    # Run a Manta job. Here `grep t` is our map phase.
    [.../trent/stor]$ job numbers.txt ^ grep t
    two
    three

    # Add a reduce phase, indicated by '^^'.
    [.../trent/stor]$ job numbers.txt ^ grep t ^^ wc -l
    2


# License

MIT. See LICENSE.txt.

Some pure Python dependencies are included in this distribution (to
reduce install dependency headaches). They are covered by their
respective licenses:

- paramiko (http://www.lag.net/paramiko/): LGPL
- httplib2 (http://code.google.com/p/httplib2/): MIT
- cmdln (https://github.com/trentm/cmdln): MIT
- appdirs (https://github.com/ActiveState/appdirs): MIT
- pycrypto build for sunos: public domain
  (https://github.com/dlitz/pycrypto/blob/master/COPYRIGHT)


# Limitations

The python-manta Python API isn't currently well-suited to huge objects
or huge directory listings (>10k dirents) because responses are fully
buffered in memory rather than being streamed. If streaming is a requirement
for your use case, you could consider the [Manta Node.js
bindings](https://github.com/joyent/node-manta).

For other limitations (also planned work) see TODO.txt.


# Development

    git clone git@github.com:joyent/python-manta.git
    export PATH=`pwd`/python-manta/bin:$PATH
