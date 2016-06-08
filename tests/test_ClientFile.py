# This Source Code Form is subject to the terms of the MIT License.
# If a copy of the MIT License was not distributed with this
# file, you can obtain one at https://opensource.org/licenses/MIT.
#
"""Unit tests for ClientFile in data.py."""

import unittest
from authenticator import ClientData, ClientFile


class CoreClientFileTests(unittest.TestCase):
    """Tests for the data module."""

    @classmethod
    def setUpClass(cls):
        """Test class setup of variables and data used in multiple tests.

        Because it takes a long time to setup the ClientFile class (due to
        the key stretching mechanism of the cryptographic key setup), I
        only do it once for the entire fixture.
        """
        import time

        cls._passphrase = "The quick brown fox jumped over the lazy dog."
        time_start = time.perf_counter()
        cls._cut = ClientFile(cls._passphrase)
        time_end = time.perf_counter()
        cls._duration = time_end - time_start

    def setUp(self):
        """Test case setup of variables and data used in multiple tests."""
        return

    def test_noop(self):
        """Excercise tearDown and setUp methods.

        This test does nothing itself. It is useful to test the tearDown()
        and setUp() methods in isolation (without side effects).

        """
        return

    # -------------------------------------------------------------------------
    # Tests for ClientFile.__init__()
    # -------------------------------------------------------------------------

    def test_constructor(self):
        """Test for __init__().

        Happy path. Make sure it takes 0.1 second or more to initialize.

        """
        self.assertLessEqual(0.1, CoreClientFileTests._duration)

    # -------------------------------------------------------------------------
    # Tests for ClientFile._Encrypt() and ._Decrypt()
    # -------------------------------------------------------------------------

    def test_constructor_encrypt_decrypt(self):
        """Test for __init__().

        Ensure a simple encrypt and decrypt work as expected.

        """
        plain_text = (
            "Do not ask what you can do for yourselves.\n"
            "Ask what you can do for your country.")
        cypher_text = CoreClientFileTests._cut._encrypt(
            bytes(plain_text, 'utf-8'))
        decrypted_text = str(
            CoreClientFileTests._cut._decrypt(cypher_text), 'utf-8')
        self.assertEqual(plain_text, decrypted_text)

    # -------------------------------------------------------------------------
    # Tests for ClientFile.Save() and .Load()
    # -------------------------------------------------------------------------

    def test_save_load(self):
        """Test for Save(), Load().

        Ensure a simple Save() and Load() work as expected.

        """
        import tempfile
        import os

        expected = []
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        expected.append(ClientData(**args))
        args = {
            "clientId": "You.Dont.Say",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "counterFromTime": False,
            "lastCount": 99,
            "lastCountUpdateTime": "20130704T131415-0500",
            "note": "This is not a note.",
            "tags": ["test", "none"]
        }
        expected.append(ClientData(**args))
        args = {
            "clientId": "Well.I.Never",
            "sharedSecret": "ABCDGNBVGY3TQOJQGEZDGNBVGY3TQCBA",
            "note": "Man who sit on tack better off.",
            "passwordLength": 8,
            "period": 15,
            "tags": ["AWS"]
        }
        expected.append(ClientData(**args))

        with tempfile.TemporaryDirectory() as tempDirPath:
            filepath = tempDirPath + os.sep + "hotp.data"
            CoreClientFileTests._cut.save(filepath, expected)
            actual = CoreClientFileTests._cut.load(filepath)
            self.assertEqual(expected, actual)
