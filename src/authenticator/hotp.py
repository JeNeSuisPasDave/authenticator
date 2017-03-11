# This Source Code Form is subject to the terms of the MIT License.
# If a copy of the MIT License was not distributed with this
# file, you can obtain one at https://opensource.org/licenses/MIT.
#
"""
Command line HOTP authenticator.

This is a simple attempt to implement the "Psuedocode for Time OTP"
and "Psuedocode for Event/Counter OTP" given in the Wikipedia article
on Google Authenticator:
http://en.wikipedia.org/wiki/Google_Authenticator

Pseudocode for Time OTP

    function GoogleAuthenticatorCode(string secret)
        key := base32decode(secret)
        message := current Unix time ÷ 30
        hash := HMAC-SHA1(key, message)
        offset := last nibble of hash
        //4 bytes starting at the offset
        truncatedHash := hash[offset..offset+3]
        //remove the most significant bit
        Set the first bit of truncatedHash to zero
        code := truncatedHash mod 1000000
        pad code with 0 until length of code is 6
        return code

Pseudocode for Event/Counter OTP

    function GoogleAuthenticatorCode(string secret)
        key := base32decode(secret)
        message := counter encoded on 8 bytes
        hash := HMAC-SHA1(key, message)
        offset := last nibble of hash
        //4 bytes starting at the offset
        truncatedHash := hash[offset..offset+3]
        //remove the most significant bit
        Set the first bit of truncatedHash to zero
        code := truncatedHash mod 1000000
        pad code with 0 until length of code is 6
        return code

I've validated the psuedocode and this implementation against RFC4226 and
RFC6238.

This implementation requires:

* Python 3.5 or later
* cryptography 1.3 or later (see https://cryptography.io/en/latest/)
* python-dateutil 2.1 or later
    (see https://pypi.python.org/pypi/python-dateutil/2.1)
* six 1.10 or later (https://pypi.python.org/pypi/six/1.10.0)

See also:
    http://en.wikipedia.org/wiki/Google_Authenticator
    http://tools.ietf.org/html/rfc6238
    http://tools.ietf.org/html/rfc4226
    http://tools.ietf.org/html/rfc4648

"""


class HOTP:
    """Implements the HOTP algorithms.

    Implements the HOTP algorithms for counter-based and time-based
    HOTP calculations.

    """

    def __init__(self):
        """Create a HOTP object."""
        return

    def code_from_hash(self, hash, code_length=6):
        """Generate a numeric code, the OTP, given a truncated hash.

        Given a byte string 4 bytes in length, preferably generated from
        hashFromHMAC(), with high-order bit clear, this method will
        produce a string of codeLength digits.

        Args:
            hash: a byte string, length 4, with high bit cleared. Ostensibly
                extracted from an HMAC (and generated, for example, by
                hasFromHMAC()).
            code_length: the number of digits in the code string. Must be in
                the range [1,10].

        Returns:
            A string of digits, code_length long, that is the one-time
            password (OTP).

        Raises:
            ValueError: hash is not 4 bytes, or code_length not in
                range [1,10].
            TypeError: hash is not a byte string, or code_length is not a
                number.

        """
        if ((1 > code_length) or
                (10 < code_length)):
            raise ValueError('code_length must be in the range [1,10]')
        if not isinstance(hash, bytes):
            raise TypeError('hash must be a byte string')
        if 4 != len(hash):
            raise ValueError(
                'hmac must be a byte string of length 8 (4 bytes)')

        int_hash = int.from_bytes(hash, 'big', signed=False)
        code = int_hash % (10**code_length)
        code_string = str(code)
        # pad on left as needed to achieve codeLength digits
        code_string = "0" * (code_length - len(code_string)) + code_string
        return code_string

    def counter_from_time(self, period=30):
        """Create 8-byte counter from current time.

        Create an 8-byte counter suitable for HMAC generation from
        current time.

        Using the current time (as number of seconds since the UNIX epoch)
        calculate an interval number using an interval size of period (default
        30 seconds). The counter is the interval number as a 64-bit integer,
        represented as an 8-byte string. The byte string is formatted with
        the most significant byte first and least significant byte
        last.

        The seconds remaining in the period is: period - remainder of the
        interval division.

        Args:
            period: The size, in seconds, of the period used to calculate
            the counter value from the current time. Default is 30 seconds.

        Returns:
            An tuple containing:
                * 8-byte byte string representing the counter as a 64-bit
                  unsigned integer. The most signficant byte is first,
                  least significant byte is last.
                * The integer seconds remaining in the current interval

        Raises:
            ValueError: period is not a positive integer
            TypeError: period is not numeric or not a numeric string

        """
        import time
        import datetime

        # make sure period is an integer
        period = int(period)
        if (0 >= period):
            raise ValueError('period must be positive integer')

        local_now = datetime.datetime.now()
        seconds_now = time.mktime(local_now.timetuple())
        intervals = seconds_now // period
        remaining_seconds = seconds_now - (intervals * period)
        counter = self.num_to_counter(intervals)
        return (counter, remaining_seconds)

    def convert_base32_secret_key(self, base32_secret_key):
        """Decode a Base32 string into a byte string.

        Base32 is an encoding system using the letters A-Z and
        digits 2-7 to encode 5-bits. Base32 strings must be in
        multiples of 40 bits; thus in multiples of 8 characters.

        See also:
            http://en.wikipedia.org/wiki/Base32
            http://tools.ietf.org/html/rfc4648

        Args:
            base32_secret_key: a string of base32 encoding

        Returns:
            A byte string representing the decoded binary data.

        Raises:
            ValueError: if base32_secret_key is not a multiple of 8 characters
            TypeError: if base32_secret_key does not contain valid base32
                encoding (invalid characters)
        """
        import base64
        import binascii

        # Pad the base32 string to a multiple of 8 characters
        #
        secret_length = len(base32_secret_key)
        pad_length = (8 - (secret_length % 8)) % 8
        pad = "=" * pad_length
        base32_secret_key = base32_secret_key + pad

        # Decode it
        #
        try:
            secret_key = base64.b32decode(base32_secret_key)
        except binascii.Error:
            raise ValueError(
                'Wrong length, incorrect padding, or embedded whitespace')
        return secret_key

    def generate_code_from_counter(self, secret_key, counter, code_length=6):
        """Produce the counter-based OTP given a secret key.

        Args:
            secret_key: The shared secret between the client and server. This
                can be either a string containing the secret in base32
                encoding, or a unencoded byte string. RFC4648 recommends the
                secret be a minimum of 20 bytes in length.
            counter: The event or counter value tracked by client and server.
                This can be either an integer, or it can be the value formatted
                as a byte string, 8 bytes in length, with the most significant
                byte first and least significant byte last. Must be in the
                range [0,2**64 - 1].
            code_length: the number of digits in the OTP string. Must be in
                the range [1,10].
            period: The size, in seconds, of the period used to calculate the
                counter value from the current time.

        Returns:
            The time-based OTP, as a string of digits.

        Raises:
            TypeError: secret_key not a byte string or normal string. Or the
                secret is a string but is invalid base32 encoding.
            ValueError: counter is not an integer, cannot be converted to an
                integer, or is outside the range [0, 2**64 - 1]. If counter is
                a byte string, then length is not 8 bytes.
                    Or the secret key is a base32 string that has incorrect
                padding (length not a multiple of 8 characters).

        """
        if not isinstance(counter, bytes):
            # make counter a byte string
            counter = self.num_to_counter(counter)
        if 8 != len(counter):
            raise ValueError('counter must be 8 bytes')
        # make sure codeLength is an integer
        code_length = int(code_length)
        if ((1 > code_length) or
                (10 < code_length)):
            raise ValueError('code_length must be in the range [1,10]')
        if not isinstance(secret_key, bytes):
            secret_key = self.convert_base32_secret_key(secret_key)

        # message is the counter value (as byte string, length 8)
        #
        message = counter
        # hash := HMAC-SHA1(key, message)
        #
        hmac = self.generate_hmac(secret_key, message)
        # offset := last nibble of hash
        # truncated_hash := hash[offset..offset+3]
        # (that is 4 bytes starting at the offset)
        # Set the first bit of truncatedHash to zero
        # (remove the most significant bit)
        #
        truncated_hash = self.hash_from_hmac(hmac)
        # code := truncated_hash mod 1000000
        # pad code with 0 until length of code is 6
        #
        code_string = self.code_from_hash(
            truncated_hash, code_length=code_length)
        # return code
        #
        return code_string

    def generate_code_from_time(self, secret_key, code_length=6, period=30):
        """Produce the time-based OTP given a secret key.

        Args:
            secret_key: The shared secret between the client and server. This
                can be either a string containing the secret in base32
                encoding, or a unencoded byte string. RFC4648 recommends the
                secret be a minimum of 20 bytes in length.
            code_length: the number of digits in the OTP string. Must be in
                the range [1,10].
            period: The size, in seconds, of the period used to calculate the
                counter value from the current time.

        Returns:
            A tuple containing:
                * The time-based OTP, as a string of digits.
                * The integer number of seconds remaining in the current
                  interval.

        Raises:
            TypeError: secret_key not a byte string or normal string.

        """
        # make sure period is an integer
        period = int(period)
        if (0 >= period):
            raise ValueError('period must be positive integer')
        # make sure codeLength is an integer
        code_length = int(code_length)
        if ((1 > code_length) or
                (10 < code_length)):
            raise ValueError('code_length must be in the range [1,10]')
        if not isinstance(secret_key, bytes):
            secret_key = self.convert_base32_secret_key(secret_key)

        # message := current Unix time ÷ 30
        #
        message, remaining_seconds = self.counter_from_time(period=period)
        # hash := HMAC-SHA1(key, message)
        #
        hmac = self.generate_hmac(secret_key, message)
        # offset := last nibble of hash
        # truncatedH_hsh := hash[offset..offset+3]
        # (that is 4 bytes starting at the offset)
        # Set the first bit of truncatedHash to zero
        # (remove the most significant bit)
        #
        truncated_hash = self.hash_from_hmac(hmac)
        # code := truncated_hash mod 1000000
        # pad code with 0 until length of code is 6
        #
        code_string = self.code_from_hash(
            truncated_hash, code_length=code_length)
        # return code, remaining seconds
        #
        return code_string, int(period - remaining_seconds)

    def generate_hmac(self, secret_key, counter):
        """Create a 160-bit HMAC from secret and counter.

        Args:
            secret_key: a byte string (recommended minimum 20 bytes) that is
                the shared secret between the client and server.
            counter: an integer value represented in an 8-byte string with
                the most significant byte first and least significant byte
                last

        Returns:
            The HMAC digest; a byte string, 20 bytes long.

        Raises:
            TypeError: if the counter and secret are not byte strings.
            ValueError: if the counter is not 8 bytes long.

        """
        from hashlib import sha1
        import hmac

        if not isinstance(secret_key, bytes):
            raise TypeError('secret_key must be a byte string')
        if not isinstance(counter, bytes):
            raise TypeError('counter must be a byte string')
        if (8 != len(counter)):
            raise ValueError('counter must be 8 bytes')

        hmac = hmac.new(secret_key, counter, sha1)
        hash = hmac.digest()
        return hash

    def hash_from_hmac(self, hmac):
        """Get a 4-byte hash from the HMAC.

        Using the algorithm in RFC4226, choose a 4-byte segment of the
        HMAC and clear the high-order bit.

        Args:
            hmac: A byte string representing the 20-byte HMAC

        Returns:
            A byte string of 4 bytes representing a truncated hash derived
            from the HMAC

        Raises:
            TypeError: if hmac is not a byte string
            ValueError: if hmac is not a byte string 20 bytes in length.
        """
        if not isinstance(hmac, bytes):
            raise TypeError('hmac must be a byte string')
        if 20 != len(hmac):
            raise ValueError('hmac must be a byte string of length 20')

        # offset := last nibble of hash
        #
        offset = int("0" + hex(hmac[-1])[-1], 16)
        # Get the 4 bytes starting at the offset
        #
        chunk = hmac[offset:(offset + 4)]
        # Set the first bit of truncatedHash to zero
        # (remove the most significant bit)
        #
        truncated_hash = bytes([chunk[0] & 127]) + chunk[1:]
        # Get out
        #
        return truncated_hash

    def num_to_counter(self, num):
        """Create an 8-byte counter suitable for HMAC generation.

        Given a number num, produce an 8-byte byte string representing
        the equivalent 64-bit integer. The byte string is formatted with
        the most significant byte first and least significant byte
        last.

        Args:
            num: Any positive integer or floating-point value. Floating-point
                values will be truncated (only the integer portion will be
                used).

        Returns:
            An 8-byte byte string representing the value as a 64-bit unsigned
            integer. The most signficant byte is first, least significant byte
            is last.

        Raises:
            ValueError: num is a non-numeric values, or a negative
                value, or exceeds 2**64 - 1.

        """
        inum = int(num)
        if (0 > inum) or (2**64 <= inum):
            raise ValueError('num')
        s_hex = hex(int(num))[2:]
        l_hex = len(s_hex)
        s_hex = ('0' * (16-l_hex)) + s_hex
        ba_counter = bytes.fromhex(s_hex)
        return ba_counter

# in progress

# not yet tested

    def generate_secret_key(self):
        """Generate a cryptographically random secret key."""
        import os

        secret_key = os.urandom(10)
        return secret_key
