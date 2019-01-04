# Copyright 2018 Joyent, Inc.  All rights reserved.

"""Manta client auth."""

from __future__ import absolute_import
import binascii
import sys
import io
import os
from os.path import expanduser
import logging
import base64
import hashlib
from getpass import getpass
import re
import struct
from glob import glob

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.hashes import SHA1, SHA256, SHA384, SHA512
from cryptography.hazmat.primitives.asymmetric import padding, ec, rsa
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

from paramiko import Agent
from paramiko.message import Message

from manta.errors import MantaError


#---- globals

log = logging.getLogger('manta.auth')

FINGERPRINT_RE = re.compile(r'(^(MD5:)?([a-f0-9]{2}:){15}[a-f0-9]{2})|(^SHA256:[a-zA-Z0-9\/\+]{43})$')

PEM_STRING_RSA_RE = re.compile(r'RSA (PUBLIC|PRIVATE) KEY')
PEM_STRING_ECDSA_RE = re.compile(r'EC(DSA)? (PUBLIC|PRIVATE) KEY')

ECDSA_SHA256_STR = "ecdsa-sha256"
ECDSA_SHA384_STR = "ecdsa-sha384"
ECDSA_SHA512_STR = "ecdsa-sha512"
RSA_STR = "rsa-sha1"

# TODO: add and test other SSH key types
ALGO_FROM_SSH_KEY_TYPE = {
    "ecdsa-sha2-nistp256": ECDSA_SHA256_STR,
    "ecdsa-sha2-nistp384": ECDSA_SHA384_STR,
    "ecdsa-sha2-nistp521": ECDSA_SHA512_STR,
    "ssh-rsa": RSA_STR
}

ECDSA_ALGO_FROM_KEY_SIZE = {
    "256": ECDSA_SHA256_STR,
    "384": ECDSA_SHA384_STR,
    "521": ECDSA_SHA512_STR
}


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
    if (re.search(r'^ssh-(?:rsa|dss) ', data) or
        re.search(r'^ecdsa-sha2-nistp(?:[0-9]+)', data)):
        data = data.split(None, 2)[1]

    key = base64.b64decode(data)
    fp_plain = hashlib.md5(key).hexdigest()
    return ':'.join(a + b for a, b in zip(fp_plain[::2], fp_plain[1::2]))


def fingerprint_from_raw_ssh_pub_key(key):
    """Encode a raw SSH key (string of bytes, as from
    `str(paramiko.AgentKey)`) to a fingerprint in the typical
    '54:c7:4c:93:cf:ff:e3:32:68:bc:89:6e:5e:22:b5:9c' form.
    """
    fp_plain = hashlib.md5(key).hexdigest()
    return ':'.join(a + b for a, b in zip(fp_plain[::2], fp_plain[1::2]))


def sha256_fingerprint_from_ssh_pub_key(data):
    data = data.strip()

    # accept either base64 encoded data or full pub key file,
    # same as `fingerprint_from_ssh_pub_key`.
    if (re.search(r'^ssh-(?:rsa|dss) ', data) or
        re.search(r'^ecdsa-sha2-nistp(?:[0-9]+)', data)):
        data = data.split(None, 2)[1]

    digest = hashlib.sha256(binascii.a2b_base64(data)).digest()
    encoded = base64.b64encode(digest)  # ssh-keygen strips thi
    return 'SHA256:' + encoded.decode('utf-8')

def sha256_fingerprint_from_raw_ssh_pub_key(raw_key):
    """Encode a raw SSH key (string of bytes, as from
    `str(paramiko.AgentKey)`) to a fingerprint in the SHA256 form:
        SHA256:j2WoSeOWhFy69BQ39fuafFAySp9qCZTSCEyT2vRKcL+s
    """
    digest = hashlib.sha256(raw_key).digest()
    h = base64.b64encode(digest).decode('utf-8')
    h = h.rstrip().rstrip('=')  # drop newline and possible base64 padding
    return 'SHA256:' + h

def load_ssh_key(key_id, skip_priv_key=False):
    """
    Load a local ssh private key (in PEM format). PEM format is the OpenSSH
    default format for private keys.

    See similar code in imgapi.js#loadSSHKey.

    @param key_id {str} An ssh public key fingerprint or ssh private key path.
    @param skip_priv_key {boolean} Optional. Default false. If true, then this
        will skip loading the private key file and `priv_key` will be `None`
        in the retval.
    @returns {dict} with these keys:
        - pub_key_path
        - fingerprint
        - priv_key_path
        - priv_key
        - algorithm
    """
    priv_key = None

    # If `key_id` is already a private key path, then easy.
    if not FINGERPRINT_RE.match(key_id):
        if not skip_priv_key:
            f = io.open(key_id, 'rb')
            try:
                priv_key = f.read()
            finally:
                f.close()
        pub_key_path = key_id + '.pub'
        f = io.open(pub_key_path, 'r')
        try:
            pub_key = f.read()
        finally:
            f.close()
        fingerprint = fingerprint_from_ssh_pub_key(pub_key)

        # XXX: pubkey should NOT be in PEM format.
        try:
            algo = ALGO_FROM_SSH_KEY_TYPE[pub_key.split()[0]]
        except KeyError:
            raise MantaError("Unsupported key type for: {}".format(key_id))

        return dict(
            pub_key_path=pub_key_path,
            fingerprint=fingerprint,
            priv_key_path=key_id,
            priv_key=priv_key,
            algorithm=algo)

    # Else, look at all pub/priv keys in "~/.ssh" for a matching fingerprint.
    fingerprint = key_id

    pub_key_glob = expanduser('~/.ssh/*.pub')
    pub_key = None
    for pub_key_path in glob(pub_key_glob):
        try:
            f = io.open(pub_key_path, 'r')
        except IOError:
            # This can happen if the .pub file is a broken symlink.
            log.debug("could not open '%s', skip it", pub_key_path)
            continue
        try:
            pub_key = f.read()
        finally:
            f.close()

        # The MD5 fingerprint functions return the hexdigest without the hash
        # algorithm prefix ("MD5:"), and the SHA256 functions return the
        # fingerprint with the prefix ("SHA256:").  Ideally we'd want to
        # normalize these, but more importantly we don't want to break backwards
        # compatibility for either the SHA or MD5 users.
        md5_fp = fingerprint_from_ssh_pub_key(pub_key)
        sha256_fp = sha256_fingerprint_from_ssh_pub_key(pub_key)
        if (sha256_fp == fingerprint or
            md5_fp == fingerprint or
            "MD5:" + md5_fp == fingerprint):

            # if the user has given us sha256 fingerprint, canonicalize
            # it to the md5 fingerprint
            fingerprint = md5_fp
            break
    else:
        raise MantaError(
            "no '~/.ssh/*.pub' key found with fingerprint '%s'"
            % fingerprint)

    # XXX: pubkey should NOT be in PEM format.
    try:
        algo = ALGO_FROM_SSH_KEY_TYPE[pub_key.split()[0]]
    except KeyError:
        raise MantaError("Unsupported key type for: {}".format(key_id))

    priv_key_path = os.path.splitext(pub_key_path)[0]
    if not skip_priv_key:
        f = io.open(priv_key_path, 'rb')
        try:
            priv_key = f.read()
        finally:
            f.close()
    return dict(
        pub_key_path=pub_key_path,
        fingerprint=fingerprint,
        priv_key_path=priv_key_path,
        priv_key=priv_key,
        algorithm=algo)

def rsa_sig_from_agent_signed_response(response):
    msg = Message(response)
    algo = msg.get_string()
    signature = msg.get_string()

    return signature

def ecdsa_sig_from_agent_signed_response(response):
    msg = Message(response)
    algo = msg.get_text()
    sig = msg.get_binary()

    sig_msg = Message(sig)
    r = sig_msg.get_mpint()
    s = sig_msg.get_mpint()
    signature = encode_dss_signature(r, s)

    return signature

def ssh_key_info_from_key_data(key_id, priv_key=None):
    """Get/load SSH key info necessary for signing.

    @param key_id {str} Either a private ssh key fingerprint, e.g.
        'b3:f0:a1:6c:18:3b:42:63:fd:6e:57:42:74:17:d4:bc', or the path to
        an ssh private key file (like ssh's IdentityFile config option).
    @param priv_key {str} Optional. SSH private key file data (PEM format).
    @return {dict} with these keys:
        - type: "agent"
        - signer: Crypto signer class (a PKCS#1 v1.5 signer for RSA keys)
        - fingerprint: key md5 fingerprint
        - algorithm: See ALGO_FROM_SSH_KEY_TYPE for supported list.
        - ... some others added by `load_ssh_key()`
    """
    if FINGERPRINT_RE.match(key_id) and priv_key:
        key_info = {"fingerprint": key_id, "priv_key": priv_key}
    else:
        # Otherwise, we attempt to load necessary details from ~/.ssh.
        key_info = load_ssh_key(key_id)

    # Load a key signer.
    key = None
    try:
        key = serialization.load_pem_private_key(
            key_info["priv_key"],
            password=None,
            backend=default_backend())
    except TypeError as ex:
        log.debug("could not import key without passphrase (will "
            "try with passphrase): %s", ex)
        if "priv_key_path" in key_info:
            prompt = "Passphrase [%s]: " % key_info["priv_key_path"]
        else:
            prompt = "Passphrase: "
        for i in range(3):
            passphrase = getpass(prompt)
            if not passphrase:
                break
            try:
                key = serialization.load_pem_private_key(
                    key_info["priv_key"],
                    password=passphrase,
                    backend=default_backend())
            except ValueError:
                continue
            else:
                break
        if not key:
            details = ""
            if "priv_key_path" in key_info:
                details = " (%s)" % key_info["priv_key_path"]
            raise MantaError("could not import key" + details)

    # If load_ssh_key() wasn't run, set the algorithm here.
    if 'algorithm' not in key_info:
        if isinstance(key, ec.EllipticCurvePrivateKey):
            key_info['algorithm'] = ECDSA_ALGO_FROM_KEY_SIZE[str(key.key_size)]
        elif isinstance(key, rsa.RSAPrivateKey):
            key_info['algorithm'] = RSA_STR
        else:
            raise MantaError("Unsupported key type for: {}".format(key_id))

    key_info["signer"] = key
    key_info["type"] = "ssh_key"
    return key_info

def agent_key_info_from_key_id(key_id):
    """Find a matching key in the ssh-agent.

    @param key_id {str} Either a private ssh key fingerprint, e.g.
        'b3:f0:a1:6c:18:3b:42:63:fd:6e:57:42:74:17:d4:bc', or the path to
        an ssh private key file (like ssh's IdentityFile config option).
    @return {dict} with these keys:
        - type: "agent"
        - agent_key: paramiko AgentKey
        - fingerprint: key fingerprint
        - algorithm: "rsa-sha1"  Currently don't support DSA agent signing.
    """
    # Need the fingerprint of the key we're using for signing. If it
    # is a path to a priv key, then we need to load it.
    if not FINGERPRINT_RE.match(key_id):
        ssh_key = load_ssh_key(key_id, True)
        fingerprint = ssh_key["fingerprint"]
    else:
        fingerprint = key_id

    # Look for a matching fingerprint in the ssh-agent keys.
    keys = Agent().get_keys()

    for key in keys:
        raw_key = key.blob


        # The MD5 fingerprint functions return the hexdigest without the hash
        # algorithm prefix ("MD5:"), and the SHA256 functions return the
        # fingerprint with the prefix ("SHA256:").  Ideally we'd want to
        # normalize these, but more importantly we don't want to break backwards
        # compatibility for either the SHA or MD5 users.
        md5_fp = fingerprint_from_raw_ssh_pub_key(raw_key)
        sha_fp = sha256_fingerprint_from_raw_ssh_pub_key(raw_key)
        if (sha_fp == fingerprint or
            md5_fp == fingerprint or
            "MD5:" + md5_fp == fingerprint):

            # Canonicalize it to the md5 fingerprint.
            md5_fingerprint = md5_fp
            break
    else:
        raise MantaError('no ssh-agent key with fingerprint "%s"' %
                         fingerprint)

    return {
        "type": "agent",
        "agent_key": key,
        "fingerprint": md5_fingerprint,
        "algorithm": ALGO_FROM_SSH_KEY_TYPE[key.name]
    }

def ssh_key_sign(key_info, message):
    algo = key_info["algorithm"].split('-')
    hash_algo = algo[1]
    key_type = algo[0]

    hash_class = {
        "sha1": SHA1,
        "sha256": SHA256,
        "sha384": SHA384,
        "sha512": SHA512
    }[hash_algo]

    assert isinstance(message, bytes)

    if key_type == 'ecdsa':
        signed_raw = key_info["signer"].sign(
            message,
            ec.ECDSA(hash_class())
        )
    else:
        assert (key_type == 'rsa')
        signed_raw = key_info["signer"].sign(
            message,
            padding.PKCS1v15(),
            hash_class()
        )
    signed = base64.b64encode(signed_raw)
    return signed


#---- exports


class Signer(object):
    """A virtual base class for python-manta request signing."""

    def sign(self, s):
        """Sign the given string.

        @param s {str} The string to be signed.
        @returns (algorithm, key-md5-fingerprint, signature) {3-tuple}
            For example: `("rsa-sha256", "b3:f0:...:bc",
            "OXKzi5+h1aR9dVWHOu647x+ijhk...6w==")`.
        """
        raise NotImplementedError("this is a virtual base class")


class PrivateKeySigner(Signer):
    """Sign Manta requests with the given ssh private key.

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

    _key_info_cache = None

    def _get_key_info(self):
        """Get key info appropriate for signing."""
        if self._key_info_cache is None:
            self._key_info_cache = ssh_key_info_from_key_data(self.key_id,
                                                              self.priv_key)
        return self._key_info_cache

    def sign(self, s):
        if not isinstance(s, bytes):
            assert isinstance(s, str)
            s = s.encode("utf-8")

        key_info = self._get_key_info()

        assert key_info["type"] == "ssh_key"

        signed = ssh_key_sign(key_info, s)

        return (key_info["algorithm"], key_info["fingerprint"], signed)


class SSHAgentSigner(Signer):
    """Sign Manta requests using an ssh-agent.

    @param key_id {str} Either a private ssh key fingerprint, e.g.
        'b3:f0:a1:6c:18:3b:42:63:fd:6e:57:42:74:17:d4:bc', or the path to
        an ssh private key file (like ssh's IdentityFile config option).
    """

    def __init__(self, key_id):
        self.key_id = key_id

    _key_info_cache = None

    def _get_key_info(self):
        """Get key info appropriate for signing."""
        if self._key_info_cache is None:
            self._key_info_cache = agent_key_info_from_key_id(self.key_id)
        return self._key_info_cache

    def sign(self, s):

        if not isinstance(s, bytes):
            assert isinstance(s, str)
            s = s.encode("utf-8")

        key_info = self._get_key_info()
        assert key_info["type"] == "agent"

        response = key_info["agent_key"].sign_ssh_data(s)

        if re.search(r'^ecdsa-', key_info['algorithm']):
            signed_raw = ecdsa_sig_from_agent_signed_response(response)
        else:
            signed_raw = rsa_sig_from_agent_signed_response(response)

        signed = base64.b64encode(signed_raw)

        return (key_info["algorithm"], key_info["fingerprint"], signed)


class CLISigner(Signer):
    """Sign Manta requests using the SSH agent (if available and has the
    required key) or loading keys from "~/.ssh/*".
    """

    def __init__(self, key_id):
        self.key_id = key_id

    _key_info_cache = None

    def _get_key_info(self):
        """Get key info appropriate for signing: either from the ssh agent
        or from a private key.
        """
        if self._key_info_cache is not None:
            return self._key_info_cache

        errors = []

        # First try the agent.
        try:
            key_info = agent_key_info_from_key_id(self.key_id)
        except MantaError:
            _, ex, _ = sys.exc_info()
            errors.append(ex)
        else:
            self._key_info_cache = key_info
            return self._key_info_cache

        # Try loading from "~/.ssh/*".
        try:
            key_info = ssh_key_info_from_key_data(self.key_id)
        except MantaError:
            _, ex, _ = sys.exc_info()
            errors.append(ex)
        else:
            self._key_info_cache = key_info
            return self._key_info_cache

        raise MantaError("could not find key info for signing: %s" %
                         "; ".join(map(str, errors)))

    def sign(self, sigstr):
        if not isinstance(sigstr, bytes):
            assert isinstance(sigstr, str)
            sigstr = sigstr.encode("utf-8")

        key_info = self._get_key_info()
        log.debug("sign %r with %s key (algo %s, fp %s)", sigstr,
                  key_info["type"], key_info["algorithm"],
                  key_info["fingerprint"])

        if key_info["type"] == "agent":
            response = key_info["agent_key"].sign_ssh_data(sigstr)

            if re.search(r'^ecdsa-', key_info['algorithm']):
                signed_raw = ecdsa_sig_from_agent_signed_response(response)
            else:
                signed_raw = rsa_sig_from_agent_signed_response(response)

            signed = base64.b64encode(signed_raw)
        elif key_info["type"] == "ssh_key":
            signed = ssh_key_sign(key_info, sigstr)
        else:
            raise MantaError("internal error: unknown key type: %r" %
                             key_info["type"])

        return (key_info["algorithm"], key_info["fingerprint"], signed)
