# This Source Code Form is subject to the terms of the MIT License.
# If a copy of the MIT License was not distributed with this
# file, you can obtain one at https://opensource.org/licenses/MIT.
#
"""Unit tests for the otp module.

Many tests use reference data and examples from the RFC4226.

TODO: create test data and expected results using the Java reference
      implementation; use large counters (e.g. b'80000000abcdef00').

"""

import unittest
from authenticator import HOTP


class CoreHOTPTests(unittest.TestCase):
    """Tests for the otp module."""

    def reference_generate_code_from_time(self, secret_key):
        """Reference implementation of generate_code_from_time method.

        A reference/alternate implementation of Otp.generate_code_from_time()
        which is to be used to generate expected values for unit tests.

        Returns:
            A tuple containing:
                * The time-based OTP, as a string of digits.
                * The integer number of seconds remaining in the current
                  interval.

        """
        import time
        import datetime
        from hashlib import sha1
        import hmac

        cut = HOTP()
        # message := current Unix time ÷ 30
        #
        local_now = datetime.datetime.now()
        seconds_now = time.mktime(local_now.timetuple())
        intervals = seconds_now // 30
        remaining_seconds = seconds_now - (intervals * 30)
        message = cut.num_to_counter(intervals)
        # hash := HMAC-SHA1(key, message)
        #
        hmac = hmac.new(secret_key, message, sha1)
        hash = hmac.hexdigest()
        # offset := last nibble of hash
        #
        offset = int("0" + hash[-1], 16)
        offset *= 2
        # truncated_hash := hash[offset..offset+3]
        # (that is 4 bytes starting at the offset)
        #
        truncated_hash = hash[offset: offset + (4 * 2)]
        # Set the first bit of truncated_hash to zero
        # (remove the most significant bit)
        #
        new_high_order_byte = hex(
            int(truncated_hash[0:2], 16) & int('7F', 16))[2:]
        new_high_order_byte = \
            "0" * (2 - len(new_high_order_byte)) + new_high_order_byte
        truncated_hash = new_high_order_byte + truncated_hash[2:]
        # code := truncated_hash mod 1000000
        #
        int_hash = int(truncated_hash, 16)
        code = int_hash % 1000000
        # pad code with 0 until length of code is 6
        #
        code_string = str(code)
        code_string = "0" * (6 - len(code_string)) + code_string
        # return code
        #
        return code_string, int(30 - remaining_seconds)

    def setUp(self):
        """Create data used by the test cases.

        Much of this test data comes from the test values in
        "Appendix D - HOTP Algorithm: Test Values" of RFC4226.

        """
        # the ASCII string used as the secret, in the Appendix D example
        #
        self.secret = b'12345678901234567890'
        self.secret_base32 = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"

        # The expected intermediate and final values from the HOTP algorithm
        # given the example counts and secret. From Appendix D.
        #
        # The dictionary key is the count value. The tuple values are:
        #
        #    * the count in the 8-byte integer (MSB first) form required by
        #      the algorithm,
        #    * the HMAC-SHA-1 digest
        #    * the truncated fragment of the HMAC, high bit cleared
        #    * the HOTP code
        #
        self.expected = {
            0: (
                bytes.fromhex("0000000000000000"),
                bytes.fromhex("cc93cf18508d94934c64b65d8ba7667fb7cde4b0"),
                bytes.fromhex("4c93cf18"), "755224"),
            1: (
                bytes.fromhex("0000000000000001"),
                bytes.fromhex("75a48a19d4cbe100644e8ac1397eea747a2d33ab"),
                bytes.fromhex("41397eea"), "287082"),
            2: (
                bytes.fromhex("0000000000000002"),
                bytes.fromhex("0bacb7fa082fef30782211938bc1c5e70416ff44"),
                bytes.fromhex("082fef30"), "359152"),
            3: (
                bytes.fromhex("0000000000000003"),
                bytes.fromhex("66c28227d03a2d5529262ff016a1e6ef76557ece"),
                bytes.fromhex("66ef7655"), "969429"),
            4: (
                bytes.fromhex("0000000000000004"),
                bytes.fromhex("a904c900a64b35909874b33e61c5938a8e15ed1c"),
                bytes.fromhex("61c5938a"), "338314"),
            5: (
                bytes.fromhex("0000000000000005"),
                bytes.fromhex("a37e783d7b7233c083d4f62926c7a25f238d0316"),
                bytes.fromhex("33c083d4"), "254676"),
            6: (
                bytes.fromhex("0000000000000006"),
                bytes.fromhex("bc9cd28561042c83f219324d3c607256c03272ae"),
                bytes.fromhex("7256c032"), "287922"),
            7: (
                bytes.fromhex("0000000000000007"),
                bytes.fromhex("a4fb960c0bc06e1eabb804e5b397cdc4b45596fa"),
                bytes.fromhex("04e5b397"), "162583"),
            8: (
                bytes.fromhex("0000000000000008"),
                bytes.fromhex("1b3c89f65e6c9e883012052823443f048b4332db"),
                bytes.fromhex("2823443f"), "399871"),
            9: (
                bytes.fromhex("0000000000000009"),
                bytes.fromhex("1637409809a679dc698207310c8c7fc07290d9e5"),
                bytes.fromhex("2679dc69"), "520489")}

        # Check that expected value dictionary is constructed properly
        #
        count = list(self.expected.keys())[0]
        self.assertEqual(0, count)
        counter, hmac, hmacTruncated, hotpValue = self.expected[0]
        self.assertEqual(bytes.fromhex("0000000000000000"), counter)
        self.assertEqual(bytes.fromhex(
            "cc93cf18508d94934c64b65d8ba7667fb7cde4b0"), hmac)
        self.assertEqual(bytes.fromhex("4c93cf18"), hmacTruncated)
        self.assertEqual("755224", hotpValue)
        count = list(self.expected.keys())[9]
        self.assertEqual(9, count)
        counter, hmac, hmacTruncated, hotpValue = self.expected[9]
        self.assertEqual(bytes.fromhex("0000000000000009"), counter)
        self.assertEqual(bytes.fromhex(
            "1637409809a679dc698207310c8c7fc07290d9e5"), hmac)
        self.assertEqual(bytes.fromhex("2679dc69"), hmacTruncated)
        self.assertEqual("520489", hotpValue)

        # Get out
        #
        return

    def test_noop(self):
        """Excercise tearDown and setUp methods.

        This test does nothing itself. It is useful to test the tearDown()
        and setUp() methods in isolation (without side effects).

        """
        return

    # -------------------------------------------------------------------------
    # Tests for Otp.num_to_counter()
    # -------------------------------------------------------------------------

    def test_num_to_counter(self):
        """Test Otp.num_to_counter().

        Check that various integer values work. Includes large
        and small values.

        """
        cut = HOTP()
        counter = cut.num_to_counter(2 ** 63 + 7)
        self.assertEqual(bytes.fromhex("8000000000000007"), counter)
        for i in range(0, 10):
            counter = cut.num_to_counter(i)
            self.assertEqual(self.expected[i][0], counter)
        return

    def test_num_to_counter_float(self):
        """Test Otp.num_to_counter().

        Check that floating point values work.

        """
        cut = HOTP()
        counter = cut.num_to_counter(12345678.9)
        self.assertEqual(bytes.fromhex("0000000000bc614e"), counter)
        for i in range(0, 10):
            counter = cut.num_to_counter(i + 0.6)
            self.assertEqual(self.expected[i][0], counter)
        return

    def test_num_to_counter_not_number(self):
        """Test Otp.num_to_counter().

        Check that an exception is raised if a non-numeric
        value is passed to num_to_counter().

        """
        cut = HOTP()
        num = "abcd"
        with self.assertRaises(ValueError):
            cut.num_to_counter(num)

    def test_num_to_counter_negative(self):
        """Test Otp.num_to_counter().

        Check that an exception is raised if a negative
        value is passed to num_to_counter().

        """
        cut = HOTP()
        num = -1
        with self.assertRaises(ValueError):
            cut.num_to_counter(num)

    def test_num_to_counter_too_large(self):
        """Test Otp.num_to_counter().

        Check that an exception is raised if a very
        value is passed to num_to_counter().

        """
        cut = HOTP()
        num = 2**64
        with self.assertRaises(ValueError):
            cut.num_to_counter(num)

    # -------------------------------------------------------------------------
    # Tests for Otp.hash_from_hmac()
    # -------------------------------------------------------------------------

    def test_hash_from_hmac(self):
        """Test Otp.hash_from_hmac().

        Check that expected truncated hash values are produced.

        """
        cut = HOTP()
        for i in range(0, 10):
            hash = cut.hash_from_hmac(self.expected[i][1])
            self.assertEqual(self.expected[i][2], hash)
        return

    def test_hash_from_hmac_clear_high_bit(self):
        """Test Otp.hash_from_hmac().

        Check that the high order bit is cleared in the truncated hash.

        """
        cut = HOTP()
        hmac = bytes.fromhex("ff0102030405060708090a0b0c0d0e0f101112f0")
        expected = bytes.fromhex("7f010203")
        hash = cut.hash_from_hmac(hmac)
        self.assertEqual(expected, hash)

    def test_hash_from_hmac_not_byte_string(self):
        """Test Otp.hash_from_hmac().

        Check that HMAC type (byte string) validation is performed.

        """
        cut = HOTP()
        hmac = bytearray.fromhex("ff0102030405060708090a0b0c0d0e0f101112f0")
        with self.assertRaises(TypeError):
            cut.hash_from_hmac(hmac)

    def test_hash_from_hmac_not_20bytes(self):
        """Test Otp.hash_from_hmac().

        Check that HMAC length validation is performed.

        """
        cut = HOTP()
        hmac = bytes.fromhex("ff0102030405060708090a0b0c0d0e0f101112")
        with self.assertRaises(ValueError):
            cut.hash_from_hmac(hmac)

    # -------------------------------------------------------------------------
    # Tests for Otp.convert_base32_secret_key()
    # -------------------------------------------------------------------------

    def test_convert_base32(self):
        """Test Otp.convert_base32_secret_key().

        Check that expected byte strings are produced from base32 incoded
        strings.

        Uses test data and expected results from RFC4648, section10.

        """
        cut = HOTP()
        test_data = (
            (b"", ""),
            (b"f", "MY======"),
            (b"fo", "MZXQ===="),
            (b"foo", "MZXW6==="),
            (b"foob", "MZXW6YQ="),
            (b"fooba", "MZXW6YTB"),
            (b"foobar", "MZXW6YTBOI======"))
        for expected_bytes, in_string in test_data:
            actual_bytes = cut.convert_base32_secret_key(in_string)
            self.assertEqual(expected_bytes, actual_bytes)

    def test_convert_base32_too_short(self):
        """Test Otp.convert_base32_secret_key().

        Check that an input base32 encoded string that is not multiples of 8
        characters in length (too short) throws the expected exception.

        """
        cut = HOTP()
        # First be certain the method works with a correct base32-encoded
        # input string
        #
        in_string = "ABCDEFGH"
        cut.convert_base32_secret_key(in_string)
        # Then check that it throws the expected exception with an
        # incorrectly sized input string.
        #
        in_string = "ABCDE"
        with self.assertRaises(ValueError):
            cut.convert_base32_secret_key(in_string)

    def test_convert_base32_too_long(self):
        """Test Otp.convert_base32_secret_key().

        Check that an input base32 encoded string that is not multiples of 8
        characters in length (too long) throws the expected exception.

        """
        cut = HOTP()
        # First be certain the method works with a correct base32-encoded
        # input string
        #
        in_string = "ABCDEFGH"
        cut.convert_base32_secret_key(in_string)
        # Then check that it throws the expected exception with an
        # incorrectly sized input string.
        #
        in_string = "ABCDEFGHA"
        with self.assertRaises(ValueError):
            cut.convert_base32_secret_key(in_string)

    def test_convert_base32_bad_chars(self):
        """Test Otp.convert_base32_secret_key().

        Check that an input base32 encoded string that is not encoded correctly
        throws the expected exception.

        """
        cut = HOTP()
        # First be certain the method works with a correct base32-encoded
        # input string
        #
        in_string = "ABCDEFGH"
        cut.convert_base32_secret_key(in_string)
        # Then check that it throws the expected exception with an
        # incorrectly coded input string.
        #
        # lower case not acceptable
        in_string = "abcdefgh"
        with self.assertRaises(ValueError):
            cut.convert_base32_secret_key(in_string)
        # numbers outside 2-7 not acceptable
        in_string = "ABCDEFG1"
        with self.assertRaises(ValueError):
            cut.convert_base32_secret_key(in_string)
        # padding character elsewhere than end of string
        in_string = "ABCD=FGH"
        with self.assertRaises(ValueError):
            cut.convert_base32_secret_key(in_string)

    # -------------------------------------------------------------------------
    # Tests for Otp.generate_hmac()
    # -------------------------------------------------------------------------

    def test_hmac_from_counter(self):
        """Test Otp.generate_hmac().

        Check that expected HMAC-SHA-1 digest values are produced.

        """
        cut = HOTP()
        for i in range(0, 10):
            counter = cut.num_to_counter(i)
            actual_hmac = cut.generate_hmac(self.secret, counter)
            self.assertEqual(self.expected[i][1], actual_hmac)

    def test_generate_hmac(self):
        """Test Otp.generate_hmac().

        Check that the RFC4226 test cases work for generate_hmac().

        """
        cut = HOTP()
        for i in range(0, 10):
            hmac = cut.generate_hmac(self.secret, self.expected[i][0])
            self.assertEqual(self.expected[i][1], hmac)

    def test_generate_hmac_bad_counter(self):
        """Test Otp.generate_hmac().

        Check that a counter that is other than 8 bytes raises an error.

        """
        cut = HOTP()
        # If the counter byte string is less than 8 bytes
        #
        with self.assertRaises(ValueError):
            cut.generate_hmac(self.secret, bytes.fromhex("1234"))
        # If the counter byte string is more than 8 bytes
        #
        with self.assertRaises(ValueError):
            cut.generate_hmac(
                self.secret, bytes.fromhex("12345678901234567890"))

    def test_generate_hmac_counter_not_byte_string(self):
        """Test Otp.generate_hmac().

        Check that a counter that is other than a byte string.

        """
        cut = HOTP()
        # If the counter byte string is less than 8 bytes
        #
        with self.assertRaises(TypeError):
            cut.generate_hmac(self.secret, "1234")

    def test_generate_hmac_secret_not_byte_string(self):
        """Test Otp.generate_hmac().

        Check that a counter that is other than a byte string.

        """
        cut = HOTP()
        # If the counter byte string is less than 8 bytes
        #
        with self.assertRaises(TypeError):
            cut.generate_hmac("1234567890", self.expected[1][0])

    # -------------------------------------------------------------------------
    # Tests for Otp.counter_from_time()
    # -------------------------------------------------------------------------

    def test_counter_from_time(self):
        """Test Otp.counter_from_time().

        Check that the generated counter and remaining seconds make sense
        for the given period.

        """
        cut = HOTP()
        counter, remaining_seconds30 = cut.counter_from_time()
        counter30 = int.from_bytes(counter, byteorder='big', signed=False)
        counter, remaining_seconds60 = cut.counter_from_time(60)
        counter60 = int.from_bytes(counter, byteorder='big', signed=False)
        # Check that remaining seconds are within [0,period)
        self.assertGreater(30, remaining_seconds30)
        self.assertLessEqual(0, remaining_seconds30)
        # Check that remaining seconds are within [0,period)
        self.assertGreater(60, remaining_seconds60)
        self.assertLessEqual(0, remaining_seconds60)
        # Check that counter with period 60 is just about 1/2 of counter
        # with period 30
        #
        self.assertLessEqual(counter60 * 2, counter30)
        self.assertGreater(counter60 * 2 + 2, counter30)

    def test_counter_from_time_bad_period(self):
        """Test Otp.counter_from_time().

        Check that providing a bad period raises the appropriate exception.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.counter_from_time(period=-10)
        with self.assertRaises(ValueError):
            cut.counter_from_time(period="ABC")
        with self.assertRaises(ValueError):
            cut.counter_from_time(period=-10)
        with self.assertRaises(TypeError):
            cut.counter_from_time(period=(6, 3))

    def test_counter_from_time_period_wrong_type(self):
        """Test Otp.counter_from_time().

        Check that providing a period that is not numeric or convertable
        to numeric raises the appropriate exception.

        """
        cut = HOTP()
        with self.assertRaises(TypeError):
            cut.counter_from_time(period=(6, 3))

    # -------------------------------------------------------------------------
    # Tests for Otp.code_from_hash()
    # -------------------------------------------------------------------------

    def test_code_from_hash(self):
        """Test Otp.code_from_hash().

        Check that the RFC4226 test cases work for code_from_hash()

        """
        cut = HOTP()
        for i in range(0, 10):
            code = cut.code_from_hash(self.expected[i][2])
            self.assertEqual(self.expected[i][3], code)

    def test_code_from_hash_with_alternate_lengths(self):
        """Test Otp.code_from_hash().

        Try with alternate code lengths.

        """
        cut = HOTP()
        # code_length 1
        #
        should_be = ("4", "2", "2", "9", "4", "6", "2", "3", "1", "9")
        for i in range(0, 10):
            code = cut.code_from_hash(self.expected[i][2], 1)
            self.assertEqual(should_be[i], code)
        # code_length 9
        #
        should_be = (
            "284755224",
            "094287082",
            "137359152",
            "726969429",
            "640338314",
            "868254676",
            "918287922",
            "082162583",
            "673399871",
            "645520489")
        for i in range(0, 10):
            code = cut.code_from_hash(self.expected[i][2], 9)
            self.assertEqual(should_be[i], code)

    def test_code_from_hash_zero_code_length(self):
        """Test Otp.code_from_hash().

        Check that the RFC4226 test cases work for code_from_hash()

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.code_from_hash(self.expected[0][2], 0)

    def test_code_from_hash_long_code_length(self):
        """Test Otp.code_from_hash().

        Check that the RFC4226 test cases work for code_from_hash()

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.code_from_hash(self.expected[0][2], 11)

    def test_code_from_hash_bad_code_length(self):
        """Test Otp.code_from_hash().

        Check that the RFC4226 test cases work for code_from_hash()

        """
        cut = HOTP()
        with self.assertRaises(TypeError):
            cut.code_from_hash(self.expected[0][2], "abc")

    def test_code_from_hash_bad_hash(self):
        """Test Otp.code_from_hash().

        Check that the RFC4226 test cases work for code_from_hash()

        """
        cut = HOTP()
        with self.assertRaises(TypeError):
            cut.code_from_hash("abc")

    def test_code_from_hash_wrong_length(self):
        """Test Otp.code_from_hash().

        Check that the RFC4226 test cases work for code_from_hash()

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.code_from_hash(bytes.fromhex("abcdef"))

    # -------------------------------------------------------------------------
    # Tests for Otp.generate_code_from_counter()
    # -------------------------------------------------------------------------

    def test_generate_code_from_counter_byte_string(self):
        """Test Otp.generate_code_from_counter().

        Check that the RFC4226 test cases work for generate_code_from_counter()
        when passed counter as a byte string and secret as byte string.

        """
        cut = HOTP()
        # test with counter as byte string and secret as byte string.
        #
        for i in range(0, 10):
            code_string = cut.generate_code_from_counter(
                self.secret, self.expected[i][0])
            self.assertEqual(self.expected[i][3], code_string)

    def test_generate_code_from_counter_integer(self):
        """Test Otp.generate_code_from_counter().

        Check that the RFC4226 test cases work for generate_code_from_counter()
        when passed counter as an integer and secret as byte string.

        """
        cut = HOTP()
        # test with counter as integer value and secret as byte string
        #
        for i in range(0, 10):
            code_string = cut.generate_code_from_counter(self.secret, i)
            self.assertEqual(self.expected[i][3], code_string)

    def test_generate_code_from_counter_integer_b32_secret(self):
        """Test Otp.generate_code_from_counter().

        Check that the RFC4226 test cases work for generate_code_from_counter()
        when passed counter as an integer and secret as base32 string.

        """
        cut = HOTP()
        # test with counter as integer value and secret as base32 string
        #
        for i in range(0, 10):
            code_string = cut.generate_code_from_counter(self.secret_base32, i)
            self.assertEqual(self.expected[i][3], code_string)

    def test_generate_code_from_counter_secret_wrong_type(self):
        """Test Otp.generate_code_from_counter().

        Check for appropriate exception to wrong secret type.

        """
        cut = HOTP()
        with self.assertRaises(TypeError):
            cut.generate_code_from_counter(
                1.234, self.expected[0][0])

    def test_generate_code_from_counter_counter_wrong_type(self):
        """Test Otp.generate_code_from_counter().

        Check for appropriate exception to wrong counter type.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_counter(
                self.secret, "abcdefgh")

    def test_generate_code_from_counter_counter_bad(self):
        """Test Otp.generate_code_from_counter().

        Check for appropriate exception to invalid counter value.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_counter(
                self.secret, -1)

    def test_generate_code_from_counter_counter_short(self):
        """Test Otp.generate_code_from_counter().

        Check for appropriate exception to counter byte string that is
        too short.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_counter(
                self.secret, bytes.fromhex("01020304050607"))

    def test_generate_code_from_counter_counter_long(self):
        """Test Otp.generate_code_from_counter().

        Check for appropriate exception to counter byte string that is
        too short.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_counter(
                self.secret, bytes.fromhex("010203040506070809"))

    def test_generate_code_from_counter_secret_bad_base32(self):
        """Test Otp.generate_code_from_counter().

        Check for appropriate exception to secret string that is invalid
        base32 encoding.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_counter(
                "GEZDGNBVGY1TQOJQGEZDGNBVGY1TQOJQ", self.expected[0][0])

    def test_generate_code_from_counter_secret_wrong_base32_length(self):
        """Test Otp.generate_code_from_counter().

        Check for appropriate exception to secret string that is invalid
        base32 encoding (too long, bad padding).

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_counter(
                "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQAAA", self.expected[0][0])

    def test_generate_code_from_counter_code_length_wrong_type(self):
        """Test Otp.generate_code_from_counter().

        Check for appropriate exception to wrong code_length type.

        """
        cut = HOTP()
        with self.assertRaises(TypeError):
            cut.generate_code_from_counter(
                self.secret, self.expected[0][0], code_length=(6, 3))

    def test_generate_code_from_counter_code_length_not_numeric(self):
        """Test Otp.generate_code_from_counter().

        Check for appropriate exception to non-numeric code_length.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_counter(
                self.secret, self.expected[0][0], code_length="abc")

    def test_generate_code_from_counter_code_length_out_of_range(self):
        """Test Otp.generate_code_from_counter().

        Check for appropriate exception to out-of-range code_length.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_counter(
                self.secret, self.expected[0][0], code_length="0")
        with self.assertRaises(ValueError):
            cut.generate_code_from_counter(
                self.secret, self.expected[0][0], code_length=11)

    # -------------------------------------------------------------------------
    # Tests for Otp.generate_code_from_time()
    # -------------------------------------------------------------------------

    def test_generate_code_from_time(self):
        """Test Otp.generate_code_from_time().

        Check generate_code_from_time() against a reference implementation
        when passed secret as byte string.

        """
        cut = HOTP()
        # test with secret as byte string
        #
        code_string, remaining_seconds = cut.generate_code_from_time(
            self.secret)
        expected_code, expected_seconds = \
            self.reference_generate_code_from_time(self.secret)
        if expected_seconds != remaining_seconds:
            # try again because the clocks were not the same when actual
            # and reference calls were made
            code_string, remaining_seconds = cut.generate_code_from_time(
                self.secret)
            expected_code, expected_seconds = \
                self.reference_generate_code_from_time(self.secret)
        self.assertEqual(expected_seconds, remaining_seconds)
        self.assertEqual(expected_code, code_string)

    def test_generate_code_from_time_b32_secret(self):
        """Test Otp.generate_code_from_time().

        Check generate_code_from_time() against a reference implementation
        when passed secret as base32 string.

        """
        cut = HOTP()
        # test with secret as base32 string
        #
        code_string, remaining_seconds = cut.generate_code_from_time(
            self.secret_base32)
        expected_code, expected_seconds = \
            self.reference_generate_code_from_time(self.secret)
        if expected_seconds != remaining_seconds:
            # try again because the clocks were not the same when actual
            # and reference calls were made
            code_string, remaining_seconds = cut.generate_code_from_time(
                self.secret_base32)
            expected_code, expected_seconds = \
                self.reference_generate_code_from_time(self.secret)
        self.assertEqual(expected_seconds, remaining_seconds)
        self.assertEqual(expected_code, code_string)

    def test_generate_code_from_time_secret_wrong_type(self):
        """Test Otp.generate_code_from_time().

        Check for appropriate exception to wrong secret type.

        """
        cut = HOTP()
        with self.assertRaises(TypeError):
            cut.generate_code_from_time(1.234)

    def test_generate_code_from_time_secret_bad_base32(self):
        """Test Otp.generate_code_from_time().

        Check for appropriate exception to secret string that is invalid
        base32 encoding.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_time(
                "GEZDGNBVGY1TQOJQGEZDGNBVGY1TQOJQ")

    def test_generate_code_from_time_secret_wrong_base32_length(self):
        """Test Otp.generate_code_from_time().

        Check for appropriate exception to secret string that is invalid
        base32 encoding (too long, bad padding).

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_time(
                "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQAAA")

    def test_generate_code_from_time_code_length_wrong_type(self):
        """Test Otp.generate_code_from_time().

        Check for appropriate exception to wrong code_length type.

        """
        cut = HOTP()
        with self.assertRaises(TypeError):
            cut.generate_code_from_time(
                self.secret, code_length=(6, 3))

    def test_generate_code_from_time_code_length_not_numeric(self):
        """Test Otp.generate_code_from_time().

        Check for appropriate exception to non-numeric code_length.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_time(
                self.secret, code_length="abc")

    def test_generate_code_from_time_code_length_out_of_range(self):
        """Test Otp.generate_code_from_time().

        Check for appropriate exception to out-of-range code_length.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_time(
                self.secret, code_length="0")
        with self.assertRaises(ValueError):
            cut.generate_code_from_time(
                self.secret, code_length=11)

    def test_generate_code_from_time_period_wrong_type(self):
        """Test Otp.generate_code_from_time().

        Check for appropriate exception to wrong period type.

        """
        cut = HOTP()
        with self.assertRaises(TypeError):
            cut.generate_code_from_time(
                self.secret, period=(6, 3))

    def test_generate_code_from_time_period_not_numeric(self):
        """Test Otp.generate_code_from_time().

        Check for appropriate exception to non-numeric period.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_time(
                self.secret, period="abc")

    def test_generate_code_from_time_period_out_of_range(self):
        """Test Otp.generate_code_from_time().

        Check for appropriate exception to out-of-range period.

        """
        cut = HOTP()
        with self.assertRaises(ValueError):
            cut.generate_code_from_time(
                self.secret, period="0")
        with self.assertRaises(ValueError):
            cut.generate_code_from_time(
                self.secret, period=-1)
