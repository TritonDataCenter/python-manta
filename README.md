python-manta is a community-maintained Python SDK for [the Joyent Manta
Object Storage Service](http://www.joyent.com/manta) (a.k.a. Manta). This
provides a Python 'manta' package (for using the [Manta REST
API](http://apidocs.joyent.com/manta/api.html) and a 'mantash' (MANTA SHell) CLI
and shell. For an introduction to Manta in general, see [Manta getting started
docs](http://apidocs.joyent.com/manta/index.html).


# Current Status

Tested mostly on Mac and SmartOS using Python 2.7. Linux should work.
The *intention* is to support Windows as well. Python 3 support is new and we
welcome feedback.

Python 2.6 support has been dropped in python-manta 2.7.

Feedback and issues here please: <https://github.com/joyent/python-manta/issues>


# Installation

tl;dr: `pip install --upgrade manta`


## 0. install `pip` (and maybe pynacl)

**SmartOS**:

1. Install pip:
    pkgin install py27-pip
    or
    pkgin install py34-pip

2. Install libsodium and pynacl
    pkgin install libsodium
    SODIUM_INSTALL=system pip install pynacl

**Mac**:

    # See <http://www.pip-installer.org/en/latest/installing.html>
    curl -O https://bootstrap.pypa.io/get-pip.py
    sudo python get-pip.py

**Ubuntu**:

    sudo apt-get install python3-pip 
    or
    sudo apt-get install python-pip

Others? Please [let me know](https://github.com/joyent/python-manta/issues/new)
if there are better instructions that I can provide for your system, so I can
add them here.



## 1. install python-manta

The preferred way is:

    pip install manta

If you don't have pip (see above), but have `easy_install` then:

    easy_install manta

You should also be able to install from source:

    git clone https://github.com/joyent/python-manta.git
    cd python-manta
    python setup.py install    # might require a 'sudo' prefix


## 2. verify install worked

The 'mantash' CLI should now work:

    $ mantash help
    ...

And `import manta` should now work:

    $ python -c "import manta; print(manta.__version__)"
    2.0.0



# Setup

First setup your environment to match your Joyent Manta account. Adjust
accordingly for your SSH key and Manta login. The SSH key here must match
one of keys uploaded for your Joyent Public Cloud account.

    export MANTA_KEY_ID=`ssh-keygen -l -f ~/.ssh/id_rsa.pub | awk '{print $2}'`
    export MANTA_URL=https://us-east.manta.joyent.com
    export MANTA_USER=jill
    export MANTA_SUBUSER=bob # optional, if using RBAC subuser
    export MANTA_ROLE=ops # optional, if specifying a non-default role for the subuser

`mantash` uses these environment variables (as does the [Manta Node.js SDK
CLI](https://apidocs.joyent.com/manta/index.html#setting-up-your-environment)).
Alternatively you can specify these parameters to `mantash` via command-line
options -- see `mantash --help` for details.

For a colourful `mantash` prompt you can also set:

    export MANTASH_PS1='\e[90m[\u@\h \e[34m\w\e[90m]$\e[0m '

or more simply:

    export MANTASH_PS1='[\u@\h \w]$ '

See `_update_prompt` in bin/mantash for the list of supported PS1 escape
codes.


Now test that things are working:

    $ mantash ls /$MANTA_USER
    jobs
    public
    reports
    stor

If not, see for the [Troubleshooting](#troubleshooting) section below.


# Python Usage

```python
import os
import logging
import manta

# Manta logs at the debug level, so the logging env needs to be setup.
logging.basicConfig()

url = os.environ['MANTA_URL']
account = os.environ['MANTA_USER']
key_id = os.environ['MANTA_KEY_ID']

# optional fields for RBAC
subuser = os.environ.get('MANTA_SUBUSER', None)
role = os.environ.get('MANTA_ROLE', None)

# This handles ssh-key signing of requests to Manta. Manta uses
# the HTTP Signature scheme for auth.
# http://tools.ietf.org/html/draft-cavage-http-signatures-00
signer = manta.SSHAgentSigner(key_id)

client = manta.MantaClient(url, account, subuser=subuser,
                           role=role, signer=signer)

content = client.get_object('/%s/stor/foo.txt' % account)
print content

print dir(client)   # list all methods, better documentation coming (TODO)
```

See more examples in the [examples/](./examples/) directory.


# CLI

This package also provides a `mantash` (MANTA SHell) CLI for working with
Manta:

```shell
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
[jill@us-east /jill/stor]$ ls
[jill@us-east /jill/stor]$                      # our stor is empty
[jill@us-east /jill/stor]$ put numbers.txt ./   # upload local file
[jill@us-east /jill/stor]$ ls
numbers.txt
[jill@us-east /jill/stor]$ cat numbers.txt
one
two
three
four

# List available commands. A number of the typical Unix-y commands are
# there.
[jill@us-east /jill/stor]$ help
...

# Manta jobs.
#
# Note: The '^' is used as an alternative pipe separator to '|'.
# The primary reason is to avoid Bash eating the pipe when running
# one-off `mantash job ...` commands in Bash.

# Run a Manta job. Here `grep t` is our map phase.
[jill@us-east /jill/stor]$ job numbers.txt ^ grep t
two
three

# Add a reduce phase, indicated by '^^'.
[jill@us-east /jill/stor]$ job numbers.txt ^ grep t ^^ wc -l
2
```



# License

MIT. See [LICENSE](./LICENSE).

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


# Troubleshooting

An attempt to cover some common install/setup issues.

## `pynacl` dependency install failure on SmartOS

This test failure:
```
    PASS: pwhash_argon2id
    /tmp/pip-install-AIWK8Y/pynacl/src/libsodium/build-aux/test-driver: line 107: 53648: Memory fault(coredump)
    FAIL: randombytes
    PASS: scalarmult
```

Ultimately results in this install error:
```

  File "/opt/local/lib/python2.7/subprocess.py", line 186, in check_call
      raise CalledProcessError(retcode, cmd)
subprocess.CalledProcessError: Command '['make', 'check']' returned non-zero exit status 2

            ----------------------------------------
            Command "/opt/local/bin/python2.7 -u -c "import setuptools, tokenize;__file__='/tmp/pip-install-AIWK8Y/pynacl/setup.py';f=getattr(tokenize, 'open', open)(__file__);code=f.read().replace('\r\n', '\n');f.close();exec(compile(code, __file__, 'exec'))" install --record /tmp/pip-record-YflZ4O/install-record.txt --single-version-externally-managed --compile" failed with error code 1 in /tmp/pip-install-AIWK8Y/pynacl/

```

See: https://github.com/joyent/python-manta/issues/55

## `x509 certificate routines:X509_load_cert_crl_file` error

```
$ mantash ls
mantash: ERROR: [Errno 185090050] _ssl.c:343: error:0B084002:x509 certificate routines:X509_load_cert_crl_file:system lib (/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/ssl.py:141 in __init__)

Traceback (most recent call last):
  File "/Library/Python/2.7/site-packages/manta-2.4.1-py2.7.egg/EGG-INFO/scripts/mantash", line 2001, in <module>
    retval = main(sys.argv)
...
  File "/Library/Python/2.7/site-packages/httplib2-0.8-py2.7.egg/httplib2/__init__.py", line 80, in _ssl_wrap_socket
    cert_reqs=cert_reqs, ca_certs=ca_certs)
  File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/ssl.py", line 387, in wrap_socket
    ciphers=ciphers)
  File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/ssl.py", line 141, in __init__
    ciphers)
SSLError: [Errno 185090050] _ssl.c:343: error:0B084002:x509 certificate routines:X509_load_cert_crl_file:system lib
```

This is saying that python-manta (the httplib2 package it is using) cannot
verify the MANTA\_URL server certificate. In some cases the problem here is
write access to the "cacerts.txt" file in the installed httplib2 package. That
can be solved by making that file world readable (as [discussed
here](http://stackoverflow.com/a/19145997)).

```
$ sudo chmod 644 $(python -c 'from os.path import dirname; import httplib2; print dirname(httplib2.__file__)')/cacerts.txt
Password:
```

# Development and Testing Notes

In order to make sure testing covers RBAC, you'll want to make sure you have a
subuser set up with appropriate permissions for Manta in addition to the
environment variable setup described above.

```
mkdir ./tmp

# create a dedicated test user
sdc-user create --login=python_manta --password=${PASSWORD} --email=${EMAIL}

# create a new ssh key and upload it for our user
ssh-keygen -t rsa -b 4096 -C "${EMAIL}" -f ./tmp/python_manta
sdc-user upload-key \
         $(ssh-keygen -E md5 -lf ./tmp/manta | awk -F' ' '{gsub("MD5:","");{print $2}}') \
         --name=python_manta python_manta ./tmp/python_manta.pub

# create a policy with minimum permissions we need
sdc-policy create --name=python_manta \
           --rules='CAN putdirectory' \
           --rules='CAN listdirectory' \
		   --rules='CAN getdirectory' \
		   --rules='CAN deletedirectory' \
           --rules='CAN putobject' \
	       --rules='CAN putmetadata' \
           --rules='CAN getobject' \
		   --rules='CAN deleteobject' \
		   --rules='CAN putsnaplink'

# create a new role with that policy and attach it to our user
sdc-role create --name=python_manta \
		--policies=python_manta \
		--members=python_manta

# create a directory with our role assigned to it
mmkdir ${MANTA_USER}/stor/tmp --role-tag=python_manta
```


## Release process

Here is how to cut a release:

1. Make a commit to set the intended version in
   [manta/version.py](manta/version.py) and changing `## not yet released` at
   the top of "CHANGES.md" to:

    ```
    ## not yet released

    (nothing yet)


    ## $version
    ```

   Run `make versioncheck` to ensure you have the version updated correctly.

2. Commit and push that change.

3. Use the following make target to do the release:

    ```
    make cutarelease
    ```

   This will run a couple checks (clean working copy, versioncheck) and
   then will git tag and publish to pypi. If the PyPI upload fails, you can
   retry it via `make pypi-upload`.
