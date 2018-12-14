#!/usr/bin/env python
# Copyright (c) 2018 Joyent, Inc.  All rights reserved.

"""Test the python-manta auth methods."""

from __future__ import absolute_import

from os.path import abspath, curdir
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.hashes import SHA1, SHA256, SHA384, SHA512
from cryptography.hazmat.primitives.asymmetric import padding, ec
import base64

import manta
import unittest


#---- globals

DIR = abspath(curdir)

#---- internal support stuff

def get_hash_class_from_algorithm(algo):
    hash_algo = algo.split('-')[1]
    hash_class = {
        "sha1": SHA1,
        "sha256": SHA256,
        "sha384": SHA384,
        "sha512": SHA512
    }[hash_algo]

    return hash_class

# <keytype>-<fingerprint hash algorithm>
KEYS = {
    "RSA-SHA256": {
        "type": "RSA",
        "file": DIR + "/keys/id_rsa",
        "sighash": "rsa-sha1",
        "fp": "SHA256:V9G/eoiBKThNXHybnOuG1x+LmVo/RqG1RsK71MmTqqM"
    }, 
    "RSA-MD5": {
        "type": "RSA",
        "file": DIR + "/keys/id_rsa",
        "sighash": "rsa-sha1",
        "fp": "MD5:6d:22:8b:33:8d:1e:92:43:f9:bf:e0:fe:66:bf:12:c1"
    }, 
    "ECDSA-SHA256": {
        "type": "ECDSA",
        "file": DIR + "/keys/id_ecdsa",
        "sighash": "ecdsa-sha256",
        "fp": "SHA256:ZBg8kmhnyrQlkfAM8Vk+LO4JkL2NThtwwaoEcmvNs2g"
    }, 
    "ECDSA-MD5": {
        "type": "ECDSA",
        "file": DIR + "/keys/id_ecdsa",
        "sighash": "ecdsa-sha256",
        "fp": "MD5:ad:0b:43:4a:e5:06:4d:10:7e:94:a7:cf:1a:6f:d6:62"
    },
    "ECDSA-384-SHA256": {
        "type": "ECDSA",
        "file": DIR + "/keys/id_ecdsa_384",
        "sighash": "ecdsa-sha384",
        "fp": "SHA256:uXBVY53fSEsjG+CX3LlMnwfnhFB6C9Qt5/LNbO7Wz5k"
    },
    "ECDSA-384-MD5": {
        "type": "ECDSA",
        "file": DIR + "/keys/id_ecdsa_384",
        "sighash": "ecdsa-sha384",
        "fp": "MD5:b1:51:e8:b7:66:62:d1:17:e9:7f:a2:39:68:c7:6c:d6"
    },
    "ECDSA-521-SHA256": {
        "type": "ECDSA",
        "file": DIR + "/keys/id_ecdsa_521",
        "sighash": "ecdsa-sha512",
        "fp": "SHA256:ZFyH8CD08s8ccxbz1YMJUhEeivyXyzfsLCN5I0cImzw"
    },
    "ECDSA-521-MD5": {
        "type": "ECDSA",
        "file": DIR + "/keys/id_ecdsa_521",
        "sighash": "ecdsa-sha512",
        "fp": "MD5:c6:cb:41:8e:05:f4:0e:9a:b0:68:ad:0d:62:fc:1f:a0"
    },
}

def _sign_message(self, key_name, message='signme'):
    key = KEYS[key_name]
    self.assertTrue(key)

    # We want to be able to pass in either bytes or str data
    if isinstance(message, str):
        bmessage = message.encode('utf-8')
    else:
        bmessage = message

    with open(key["file"], 'rb') as f:
        priv_key = f.read()
        f.close()

    signer = manta.PrivateKeySigner(key["fp"], priv_key)
    signed = signer.sign(message)
    self.assertEqual(len(signed), 3)
    self.assertTrue(signed[0] == key["sighash"])

    signature = base64.b64decode(signed[2])
    hash_class = get_hash_class_from_algorithm(signed[0])
    vkey = serialization.load_pem_private_key(
        priv_key,
        password=None,
        backend=default_backend()
    )

    self.assertTrue(vkey)
    vkey = vkey.public_key()
    self.assertTrue(vkey)

    # vkey.verify() raises exception if verification fails
    if key["type"] == "RSA":
        verified = vkey.verify(
            signature,
            bmessage,
            padding.PKCS1v15(),
            hash_class()
        )
    elif key["type"] == "ECDSA":
        verified = vkey.verify(
            signature,
            bmessage,
            ec.ECDSA(hash_class())
        )
    else:
        self.assertFalse("Unknown Key Type: {}".format(key["type"]))

    self.assertTrue(verified is None)

    return

#---- Test cases

class PrivateKeyTestCase(unittest.TestCase):
    def test_sign_and_verify_ecdsa_sha256(self):
        _sign_message(self, "ECDSA-SHA256")

    def test_sign_and_verify_ecdsa_md5(self):
        _sign_message(self, "ECDSA-MD5")

    def test_sign_and_verify_ecdsa_384_sha256(self):
        _sign_message(self, "ECDSA-384-SHA256")

    def test_sign_and_verify_ecdsa_384_md5(self):
        _sign_message(self, "ECDSA-384-MD5")

    def test_sign_and_verify_ecdsa_521_sha256(self):
        _sign_message(self, "ECDSA-521-SHA256")

    def test_sign_and_verify_ecdsa_521_md5(self):
        _sign_message(self, "ECDSA-521-MD5")

    def test_sign_and_verify_rsa_sha265(self):
        _sign_message(self, "RSA-SHA256")

    def test_sign_and_verify_rsa_md5(self):
        _sign_message(self, "RSA-SHA256")

    def test_sign_and_verify_binary_ecdsa_sha256(self):
        _sign_message(self, "ECDSA-SHA256", message=b'signme')


## TODO: add test cases for SSHAgentSigner and CLISigner.
