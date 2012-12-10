# Copyright 2012 Joyent, Inc.  All rights reserved.

"""Manta client auth."""

import os
from os.path import exists, expanduser
import logging
import base64
import hashlib
from getpass import getpass
import re
from glob import glob

from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256, SHA, SHA512

import manta.errors as errors


#---- globals

log = logging.getLogger('manta.auth')

FINGERPRINT_RE = re.compile(r'^([a-f0-9]{2}:){15}[a-f0-9]{2}$');



#---- internal support stuff

def fingerprint_from_ssh_pub_key(data):
    """Calculate the fingerprint of SSH public key data.

    >>> data = "ssh-rsa AAAAB3NzaC1y...4IEAA1Z4wIWCuk8F9Tzw== my key comment"
    >>> fingerprint_from_ssh_pub_key(data)
    '54:c7:4c:93:cf:ff:e3:32:68:bc:89:6e:5e:22:b5:9c'

    Adapted from <http://stackoverflow.com/questions/6682815/>
    and imgapi.js#fingerprintFromSshpubkey.
    """
    data = data.strip()

    # Let's accept either:
    # - just the base64 encoded data part, e.g.
    #   'AAAAB3NzaC1yc2EAAAABIwAA...2l24uq9Lfw=='
    # - the full ssh pub key file content, e.g.:
    #   'ssh-rsa AAAAB3NzaC1yc2EAAAABIwAA...2l24uq9Lfw== my comment'
    if (re.search(r'^ssh-[rd]sa ', data)):
        data = data.split(None, 1)[1]

    key = base64.b64decode(data)
    fp_plain = hashlib.md5(key).hexdigest()
    return ':'.join(a+b for a,b in zip(fp_plain[::2], fp_plain[1::2]))


def load_ssh_key(key_id):
    """
    Load a local ssh private key (in PEM format). PEM format is the OpenSSH
    default format for private keys.

    See similar code in imgapi.js#loadSSHKey.

    @param key_id {str} An ssh public key fingerprint or ssh private key path.
    @returns {dict} with these keys:
        - pub_key_path
        - fingerprint
        - priv_key_path
        - priv_key
    """
    # If `key_id` is already a private key path, then easy.
    if not FINGERPRINT_RE.match(key_id):
        f = open(key_id)
        try:
            data = f.read()
        finally:
            f.close()
        pub_key_path = key_id + '.pub'
        f = open(pub_key_path)
        try:
            data = f.read()
        finally:
            f.close()
        fingerprint = fingerprint_from_ssh_pub_key(data)
        return dict(
            pub_key_path=pub_key_path,
            fingerprint=fingerprint,
            priv_key_path=key_id,
            priv_key=data)

    # Else, look at all pub/priv keys in "~/.ssh" for a matching fingerprint.
    fingerprint = key_id
    pub_key_glob = expanduser('~/.ssh/*.pub')
    for pub_key_path in glob(pub_key_glob):
        f = open(pub_key_path)
        try:
            data = f.read()
        finally:
            f.close()
        if fingerprint_from_ssh_pub_key(data) == fingerprint:
            break
    else:
        raise errors.MantaError(
            "no '~/.ssh/*.pub' key found with fingerprint '%s'"
            % fingerprint)
    priv_key_path = os.path.splitext(pub_key_path)[0]
    f = open(priv_key_path)
    try:
        data = f.read()
    finally:
        f.close()
    return dict(
        pub_key_path=pub_key_path,
        fingerprint=fingerprint,
        priv_key_path=priv_key_path,
        priv_key=data)



#---- exports

class Signer(object):
    """A virtual base class for python-manta request signing."""
    def sign(self, s):
        """Sign the given string.

        @param s {str} The string to be signed.
        @returns (algorithm, key-fingerprint, signature) {3-tuple}
            For example: `("rsa-sha256", "b3:f0:...:bc",
            "OXKzi5+h1aR9dVWHOu647x+ijhk...6w==")`.
        """
        raise NotImplementedError("this is a virtual base class")

class PrivateKeySigner(Signer):
    """Sign Manta requests with the given ssh private key.

    @param key_id {str} SSH key fingerprint. Optionally this can also be a
        path to an SSH private key file.  XXX caveats
    @param key_id {str} Either a private ssh key fingerprint, e.g.
        'b3:f0:a1:6c:18:3b:42:63:fd:6e:57:42:74:17:d4:bc', or the path to
        an ssh private key file (like ssh's IdentityFile config option).
    @param priv_key {str} Optional. SSH private key file data (PEM format).

    If a *fingerprint* is provided for `key_id` *and* `priv_key` is specified,
    then this is all the data required. Otherwise, this class will attempt
    to load required key data (both public and private key files) from
    keys in "~/.ssh/".
    """
    def __init__(self, key_id, priv_key=None):
        self.key_id = key_id
        self.priv_key = priv_key

    _ssh_key_cache = None
    def _get_ssh_key(self):
        if self._ssh_key_cache is None:
            if FINGERPRINT_RE.match(self.key_id) and self.priv_key:
                self._ssh_key_cache = {
                    "fingerprint": self.key_id,
                    "priv_key": self.priv_key
                }
            else:
                # Otherwise, we attempt to load necessary details from ~/.ssh.
                self._ssh_key_cache = load_ssh_key(self.key_id)
        return self._ssh_key_cache

    _rsa_signer_cache = None
    def _get_rsa_signer(self, ssh_key):
        if self._rsa_signer_cache is None:
            try:
                key = RSA.importKey(ssh_key["priv_key"])
            except ValueError:
                if "priv_key_path" in ssh_key:
                    prompt = "Passphrase [%s]: " % ssh_key["priv_key_path"]
                else:
                    prompt = "Passphrase: "
                for i in range(3):
                    passphrase = getpass(prompt)
                    try:
                        key = RSA.importKey(ssh_key["priv_key"], passphrase)
                    except ValueError:
                        continue
                    else:
                        break
                else:
                    details = ""
                    if "priv_key_path" in ssh_key:
                        details = " (%s)" % ssh_key["priv_key_path"]
                    raise errors.MantaError("could not import key" + details)
            self._rsa_signer_cache = PKCS1_v1_5.new(key)
        return self._rsa_signer_cache

    def sign(self, s):
        assert isinstance(s, str)   # for now, not unicode. Python 3?

        ssh_key = self._get_ssh_key()

        firstline = ssh_key["priv_key"].split('\n', 1)[0]
        if ' DSA ' in firstline:
            # TODO:XXX DSA support
            raise NotImplementedError("'DSA' keys not yet supported")
        elif ' RSA ' in firstline:
            algorithm = 'rsa-sha256'
            hasher = SHA256.new()
        else:
            raise errors.MantaError('unknown private key type: "%s..."'
                % firstline)

        rsa_signer = self._get_rsa_signer(ssh_key)
        hasher.update(s)
        signed_raw = rsa_signer.sign(hasher)
        signed = base64.b64encode(signed_raw)

        return (algorithm, ssh_key["fingerprint"], signed)
