import os
import unittest
"""
Using this to container miscellaneous tests until they can be abstracted into
more clear testcases.
"""

from manta import auth


class MiscTestCase(unittest.TestCase):
    def setUp(self):
        self.fingerprint = os.environ['MANTA_KEY_ID']
        self.key_signer = auth.PrivateKeySigner(self.fingerprint)

    def test_keysign_works(self):
        ks = self.key_signer
        bin = b'foobar'
        st = str(bin)
        self.assertTrue(ks.sign(bin))
        self.assertTrue(ks.sign(st))
