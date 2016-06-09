# This Source Code Form is subject to the terms of the MIT License.
# If a copy of the MIT License was not distributed with this
# file, you can obtain one at https://opensource.org/licenses/MIT.
#
"""Access to the HOTP data for server client pairs.

Represents the data for a particular HOTP server and client pair.
Stores the client data in a file. Loads client data from a file.
Encrypts data using supply passphrase.

This implementation requires:

    * Python 3.5 or later
    * cryptography 1.3 or later (see https://cryptography.io/en/latest/)
    * python-dateutil 2.1 or later
        (see https://pypi.python.org/pypi/python-dateutil/2.1)
    * six 1.10 or later (https://pypi.python.org/pypi/six/1.10.0)

"""

import json


class DecryptionError(Exception):
    """Failed to decrypt the data."""

    pass


class FileCorruptionError(Exception):
    """HOTP data file is corrupted, unreadable."""

    pass


class ClientDataDecoder(json.JSONDecoder):
    """A JSONDecoder that recognizes ClientData objects in a JSON string."""

    def __init__(self, **kw_args):
        """Compose the standard JSONDecoder with a custom object_hook.

        The custom object_hook will recognize a dictionary that represents
        a ClientData object, and decode it as a ClientData object. All other
        objects will get passed to the standard JSONDecoder.

        Args:
            Same arguments as JSONDecoder.__init__() with the exception that
            'strict' is always set to False. If an 'object_hook' is supplied
            then it will be called by _object_decode() if the object is
            not interpreted as ClientData.

        """
        self._other_object_hook = None
        kw_args_new = kw_args.copy()
        if 'object_hook' in kw_args:
            self._other_object_hook = kw_args['object_hook']
        kw_args_new['object_hook'] = self._object_decode
        # Note: strict=False because the notes attribute might contain
        #       line feeds.
        #
        kw_args_new['strict'] = False

        self._decoder = json.JSONDecoder(**kw_args_new)

    def _object_decode(self, d):
        """Convert decoded JSON to a ClientData object.

        Take the object decoded from the JSON and if it corresponds to
        ClientData objects, convert it to a ClientData object.

        Returns:
            If converted, returns a ClientData object. Otherwise, returns the
            original object d.

        """
        if ((isinstance(d, dict)) and
                ('clientId' in d)):
            cd = ClientData(**d)
            return cd
        elif self._other_object_hook is not None:
            return self._other_object_hook(d)
        else:
            return d

    def decode(self, s):
        """Inoke the decode method of encapsulated decoder.

        Invoke the decode() method of the encapsulated decoder (which
        has an object_hook).

        Returns:
            The Python representation of 's'.
        """
        o = self._decoder.decode(s)
        return o


class ClientDataEncoder(json.JSONEncoder):
    """A specialized JSONEncoder that handles ClassData objects.

    Specialize the standard JSONEncoder class to detect ClassData objects
    and convert them to a standard object type that the JSONEncoder can handle.

    """

    def default(self, o):
        """Detect and convert ClassData objects.

        Detect ClassData objects and convert them to dictionaries. If not
        ClassData then invoke the superclass default() method.

        """
        if (ClientData.__name__ == o.__class__.__name__):
            return o.to_dict()
        else:
            return json.JSONEncoder.default(self, o)


class ClientData:
    """Represents a HOTP configuration from the client point of view."""

    # -------------------------------------------------------------------------+
    # class attributes
    # -------------------------------------------------------------------------+
    __tz = None
    __utz = None

    # -------------------------------------------------------------------------+
    # static methods
    # -------------------------------------------------------------------------+

    @staticmethod
    def utz():
        """UTC time zone."""
        from datetime import timezone, timedelta

        if ClientData.__utz is None:
            ClientData.__utz = timezone(timedelta(0))
        return ClientData.__utz

    @staticmethod
    def tz():
        """Local time zone."""
        from datetime import datetime, timezone, timedelta

        if ClientData.__tz is None:
            # figure the local timezone
            #
            lt = datetime.now()
            ut = datetime.utcnow()
            lt2 = datetime.now()
            if ut.second == lt2.second:
                lt = lt2

            # Strip off the microseconds, or the deltatime won't be in
            # round seconds
            #
            lt = datetime(
                lt.year, lt.month, lt.day, lt.hour, lt.minute, lt.second)
            ut = datetime(
                ut.year, ut.month, ut.day, ut.hour, ut.minute, ut.second)

            # Get UTC offset as a timedelta object
            #
            dt = ut - lt

            # Get UTC offset in minutes
            #
            offset_minutes = 0
            if (0 == dt.days):
                offset_minutes = dt.seconds // 60
            else:
                dt = lt - ut
                offset_minutes = dt.seconds // 60
                offset_minutes *= -1
            dt = timedelta(minutes=offset_minutes)
            ClientData.__tz = timezone(dt)

        return ClientData.__tz

    # ------------------------------------------------------------------------+
    # insternal methods
    # ------------------------------------------------------------------------+

    def _init_client_id(self, kw_args):
        """Process kw_arg client_id."""
        if 'clientId' not in kw_args:
            raise ValueError("Need a clientId string.")
        self.__client_id = kw_args['clientId']
        if not isinstance(self.__client_id, str):
            raise TypeError("clientId must be a string.")
        if 0 == len(self.__client_id):
            raise ValueError("clientId must be a non-empty string.")

    def _init_shared_secret(self, kw_args):
        """Process kw_arg shared_secret."""
        if 'sharedSecret' not in kw_args:
            raise ValueError("Need a sharedSecret string.")
        self.__shared_secret = kw_args['sharedSecret']
        if not ((isinstance(self.__shared_secret, str)) or
                (isinstance(self.__shared_secret, bytes))):
            raise TypeError(
                "sharedSecret must be a string or byte string.")
        if 0 == len(self.__shared_secret):
            raise ValueError(
                "sharedSecret must be a non-empty string or byte string.")

    def _init_counter_from_time(self, kw_args):
        """Process kw_arg counter_from_time."""
        self.__counter_from_time = True
        if 'counterFromTime' in kw_args:
            if not kw_args['counterFromTime']:
                self.__counter_from_time = False

    def _init_last_count(self, kw_args):
        """Process kw_arg last_count."""
        self.__last_count = 0
        if 'lastCount' in kw_args:
            self.__last_count = int(kw_args['lastCount'])
        if 0 > self.__last_count:
            raise ValueError(
                "lastCount must be zero or a positive integer")

    def _init_last_count_update_time(self, kw_args):
        """Process kw_arg kw_arg last_count_update_time."""
        from datetime import datetime
        import iso8601

        self.__last_count_update_time = datetime(
            1, 1, 1, 0, 0, 0, 0, ClientData.utz()).strftime(self._isoFmt)
        # Fix issue on some systems, e.g. Debian, where %Y doesn't zero-pad
        if self.__last_count_update_time[0:3] != "000":
            self.__last_count_update_time = "000" + \
                self.__last_count_update_time
        if 'lastCountUpdateTime' in kw_args:
            t = datetime.min
            v = kw_args['lastCountUpdateTime']
            if isinstance(v, datetime):
                t = v
            elif isinstance(v, str):
                t = iso8601.parse_date(v)
            else:
                raise TypeError(
                    "lastCountUpdateTime must be datetime object"
                    " or a datetime string")
            if t.tzinfo is None:
                t = t.replace(tzinfo=ClientData.utz())
            self.__last_count_update_time = t.strftime(self._isoFmt)
            # Fix issue on some systems, e.g. Debian, where %Y doesn't zero-pad
            tpadding = ""
            if 10 > t.year:
                tpadding = "000"
            elif 100 > t.year:
                tpadding = "00"
            elif 1000 > t.year:
                tpadding = "0"
            if "0" != self.__last_count_update_time[0:1]:
                self.__last_count_update_time = tpadding + \
                    self.__last_count_update_time

    def _init_period(self, kw_args):
        """Process kw_arg period."""
        self.__period = 30
        if 'period' in kw_args:
            p = int(kw_args['period'])
            if (0 >= p):
                raise ValueError("period must be a positive integer")
            self.__period = p

    def _init_password_length(self, kw_args):
        """Process kw_arg password_length."""
        self.__password_length = 6
        if 'passwordLength' in kw_args:
            pwd_len = int(kw_args['passwordLength'])
            if ((1 > pwd_len) or (10 < pwd_len)):
                raise ValueError("passwordLength must be in the range [1,10]")
            self.__password_length = pwd_len

    def _init_tags(self, kw_args):
        """Process kw_arg tags."""
        self.__tags = []
        if 'tags' in kw_args:
            if (isinstance(kw_args['tags'], tuple) or
                    isinstance(kw_args['tags'], list)):
                for tag in kw_args['tags']:
                    if not isinstance(tag, str):
                        raise TypeError(
                            "tags must be a sequence of string values")
                    if 0 < len(tag):
                        self.__tags.append(tag)
            elif isinstance(kw_args['tags'], str):
                if 0 < len(kw_args['tags']):
                    self.__tags.append(kw_args['tags'])
            else:
                raise TypeError("tags must be a sequence of string values")

    def _init_note(self, kw_args):
        """Process kw_arg note."""
        self.__note = ""
        if 'note' in kw_args:
            if not isinstance(kw_args['note'], str):
                raise TypeError("note must be a string")
            self.__note = kw_args['note']

    # ------------------------------------------------------------------------+
    # dunder methods
    # ------------------------------------------------------------------------+

    def __init__(self, **kw_args):
        """Constructor for ClientData object.

        Used by ClientDataDecoder, a JSONDecoder.

        Args:
            clientId: Required. A string to identify the client and server
                combination that this ClientData object represents. For
                example, an Amazon Web Services account 12345654321 and
                user what.me.worry might be identified by a client id of
                "12345654321@what.me.worry".
            sharedSecret: Required. The shared secret provided by the server
                when the HOTP configuration was created for the client. This
                is either a Base32 encoded string representing a byte string,
                or it is the byte string itself.
            counterFromTime: Default True. Whether to use a counter-based
                HOTP or to use a time-based HOTP.
            lastCount: Default 0. The counter used in the most recent
                counter-based HOTP calculation. Must be zero or a postive
                integer.
            lastCountUpdateTime: Default datetime.min. The time that the
                last_count was most recently changed.
            period: If time-based HOTP, default is 30; otherwise default is 0.
                This is the number of seconds in the period for which the
                HOTP is calculated. In the range (0, +infinity].
            passwordLength: Default is 6. The number of digits in the HOTP
                string. Must be in the range [1,10]
            tags: Default is an empty list. This is a list of strings that
                can be used to filter a collection of ClientData objects.
            note: Default is an empty string. This is just a freeform text
                field in which any notes about the client server HOTP
                combination can be supplied.

        """
        self._isoFmt = "%Y%m%dT%H%M%S%z"

        self._init_client_id(kw_args)
        self._init_shared_secret(kw_args)
        self._init_counter_from_time(kw_args)
        self._init_last_count(kw_args)
        self._init_last_count_update_time(kw_args)
        self._init_period(kw_args)
        self._init_password_length(kw_args)
        self._init_tags(kw_args)
        self._init_note(kw_args)

    def __str__(self):
        """Stringify this object."""
        result = []
        result.append("client_id: '{0}'".format(self.__client_id))
        result.append("shared_secret: '{0}'".format(self.__shared_secret))
        result.append(
            "counter_from_time: {0}".format(self.__counter_from_time))
        result.append("last_count: {0}".format(self.__last_count))
        result.append("last_count_update_time: {0}".format(
            self.__last_count_update_time))
        result.append("period: {0}".format(self.__period))
        result.append("password_length: {0}".format(self.__password_length))
        result.append("tags: {0}".format(self.__tags))
        result.append("note: \"\"\"{0}\"\"\"".format(self.__note))
        return "\n".join(result)

    def __eq__(self, other):
        """Whether this object is equal to the other."""
        if type(self) != type(other):
            return False
        s_vars = vars(self)
        o_vars = vars(other)
        for v in vars(self):
            if s_vars[v] != o_vars[v]:
                print("unequal property {0}\n".format(v))
                if v.endswith("last_count_update_time"):
                    print("self: {0}\n".format(s_vars[v]))
                    print("othr: {0}\n".format(o_vars[v]))
                return False
        return True

    def __ne__(self, other):
        """Whether this object is not equal to the other."""
        if type(self) != type(other):
            return True
        s_vars = vars(self)
        o_vars = vars(other)
        for v in vars(self):
            if s_vars[v] != o_vars[v]:
                return True
        return False

    def __repr__(self):
        """Canonical string representation of this object."""
        result = []
        result.append(
            "ClientData(client_id='{0}',".format(self.__client_id))
        result.append(
            "shared_secret='{0}',".format(self.__shared_secret))
        result.append(
            "last_count_update_time='{0}')".format(
                self.__last_count_update_time))
        return ' '.join(result)

    # -------------------------------------------------------------------------+
    # properties
    # -------------------------------------------------------------------------+

    def client_id(self):
        """Get the string that identifies the client and server combination.

        Returns:
            The client_id as a string.

        """
        return self.__client_id

    def shared_secret(self):
        """Get the shared secret used to calculate the HOTP.

        Returns:
            The shared_secret as a byte string.

        """
        return self.__shared_secret

    def counter_from_time(self):
        """Whether HOTP is determined from current time.

        Get whether the HOTP is calculated with a counter determined
        from the current time.

        Returns:
            True or False.

        """
        return self.__counter_from_time

    def incremented_count(self):
        """Increment the counter and return the new value.

        Will update last_count() and last_count_update_time() properties.

        Only relevant if counter_from_time() is True.

        Returns:
            The incremented last_count value.

        """
        from datetime import datetime

        self.__last_count += 1

        # get the local time, with timezone
        #
        now = datetime.now(ClientData.tz())
        self.set_last_count_update_time(now)
        return self.last_count()

    def last_count(self):
        """Get the counter value from last counter-based HOTP calculation.

        Only relevant if counter_from_time() is False.

        Returns:
            The last_count integer value.

        """
        return self.__last_count

    def last_count_update_time(self):
        """Get the timestamp of the last counter-based HOTP calculation.

        Only relevant if counter_from_time() is False.

        Returns:
            The last_count_update_time datetime value.

        """
        return self.__last_count_update_time

    def set_last_count_update_time(self, update_time):
        """Set the timestamp of the last counter-based HOTP calculation.

        Only relevant if counter_from_time() is False.

        Args:
            update_time: either a datetime object (preferably with a
                timezone), or a string with time in ISO format
                "%Y%m%dT%H%M%S%z"
        """
        from datetime import datetime

        if isinstance(update_time, datetime):
            self.__last_count_update_time = update_time.strftime(self._isoFmt)
            # Fix issue on some systems, e.g. Debian, where %Y doesn't zero-pad
            tpadding = ""
            if 10 > update_time.year:
                tpadding = "000"
            elif 100 > update_time.year:
                tpadding = "00"
            elif 1000 > update_time.year:
                tpadding = "0"
            if "0" != self.__last_count_update_time[0:1]:
                self.__last_count_update_time = tpadding + \
                    self.__last_count_update_time
        else:
            self.__last_count_update_time = update_time

    def period(self):
        """The period of the time-based counter used in the HOTP calculation.

        Only relevant if counter_from_time() is True.

        """
        return self.__period

    def password_length(self):
        """The length of the HOTP code to be generated (e.g. 6)."""
        return self.__password_length

    def tags(self):
        """List of tag strings."""
        return self.__tags[:]

    def note(self):
        """Freeform note text."""
        return self.__note

    # -------------------------------------------------------------------------+
    # serialization (for JSON)
    # -------------------------------------------------------------------------+

    def to_dict(self):
        """Represent object as a key-value collection.

        Used by ClientDataEncoder, a JSONEncoder.

        """
        d = {'clientId': self.__client_id}
        d.update({'sharedSecret': self.__shared_secret})
        d.update({'counterFromTime': self.__counter_from_time})
        d.update({'lastCount': self.__last_count})
        d.update({'lastCountUpdateTime': self.__last_count_update_time})
        d.update({'period': self.__period})
        d.update({'passwordLength': self.__password_length})
        d.update({'tags': self.__tags})
        d.update({'note': self.__note})
        return d


class ClientFile:
    """Support persistence of ClientData objects in encrypted file.

    Encapsulates the work needed to persist a collection of ClientData
    objects using an encrypted file.

    """

    def __init__(self, passphrase):
        """Create a ClientFile object.

        Args:

            passphrase: The passphrase string used to encrypt and decrypt the
                data file.

        """
        self.__key_stretches = 256 * 1024
        self.__magic_number = 0x7A6A5A4A
        self.__file_version = 1
        self.__key = self._produce_key(passphrase)
        self.__iv = self._produce_iv(self.__key)
        return

    # -------------------------------------------------------------------------+
    # internal properties
    # -------------------------------------------------------------------------+

    def _get_key_stretches(self):
        """Get count of hash iterations used to slow key generation.

        Get the number of hash iterations used to stretch key
        generation (to defeat brute force key cracking).

        """
        return self.__key_stretches

    # -------------------------------------------------------------------------+
    # internal methods
    # -------------------------------------------------------------------------+

    def _decrypt(self, b, strip_padding=True):
        """Decrypt a byte string.

        Uses the AES 256-bit symmetric key cypher.

        Args:
            b: the byte string to decrypt.
            strip_padding: whether to remove the padding (padding is required
                by AES2 to make the encrypted data an exact multiple of 16
                bytes in length).

        Returns:
            The decrypted data as a byte string.

        """
        from cryptography.hazmat.primitives.ciphers \
            import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        backend = default_backend()
        cypher = Cipher(
            algorithms.AES(self.__key), modes.CBC(self.__iv), backend=backend)
        decryptor = cypher.decryptor()
        result = decryptor.update(b) + decryptor.finalize()
        if strip_padding:
            result = result[:-result[-1]]
        return result

    def _encrypt(self, b):
        """Encrypt a byte string.

        Uses the AES 256-bit symmetric key cypher.

        Args:
            b: the byte string to encrypt.

        Returns:
            The encrypted data as a byte string.

        """
        from cryptography.hazmat.primitives.ciphers \
            import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        backend = default_backend()
        cypher = Cipher(
            algorithms.AES(self.__key), modes.CBC(self.__iv), backend=backend)
        encryptor = cypher.encryptor()
        pad_length = 16 - (len(b) % 16)
        b += bytes([pad_length]) * pad_length
        result = encryptor.update(b) + encryptor.finalize()
        return result

    def _produce_key(self, passphrase):
        """Generate encrypt key.

        Creates the encryption key using a 256-bit SHA2 hash
        and a key stretching mechanism that repeatedly hashes the previous
        hash result concatenated with the passphrase.

        Args:
            passphrase: the passphrase string.

        Returns:
            The encryption key as a byte string 32 bytes in length.

        """
        from hashlib import sha256
        pp = bytes(passphrase, 'utf-8')
        hash_alg = sha256(pp)
        for i in range(self._get_key_stretches()):
            d = hash_alg.digest()
            hash_alg.update(d + pp)
        return hash_alg.digest()

    def _produce_iv(self, key):
        """Generate initialization vector.

        Generates the initialization vector for use by the
        symmetric key encryption algorithm used to encrypt and decrypt the
        data file.

        Args:
            key: the encryption key

        Returns:
            The initialization vector as a byte string 16 bytes in length.

        """
        b = key[31] & 0x0F
        e = b + 16
        iv = key[b:e]
        return iv

    def _validate_header(self, cleartext_header, decrypted_header):
        """Whether header of data file is OK and matches expected values.

        Checks that the decrypted header values match expectation, and
        that the cleartext header is identical to the decrypted header.

        Args:
            cleartext_header: A bytes object containing the first 16 bytes
                of the data file.
            decrypted_header: A bytes object containing the next 16 bytes
                of the data file, decrypted.

        Raises:
            DecryptionError: When the decrypted header doesn't match expected
                values, so the passphrase is probably incorrect, or the key
                stretch count (of hash iterations) is incorrect, or both.

        """
        import struct

        magic_number1 = struct.unpack("!I", decrypted_header[:4])[0]
        # file_version = struct.unpack("!I", decrypted_header[4:8])[0]
        # key_stretches = struct.unpack("!I", decrypted_header[8:12])[0]
        magic_number2 = struct.unpack("!I", decrypted_header[12:])[0]
        if (self.__magic_number != magic_number1 or
                self.__magic_number != magic_number2):
            raise DecryptionError()
        if cleartext_header != decrypted_header:
            raise FileCorruptionError()

    # -------------------------------------------------------------------------+
    # public methods
    # -------------------------------------------------------------------------+

    def load(self, filepath):
        """Load ClientData objects from encrypted file.

        Load the list of ClientData objects from a file
        encrypted with the passphrase.

        Args:
            filepath: the fully qualified path to the data file.

        Returns:
            The list of ClientData objects found in the data file.

        """
        cypher_text = b''
        with open(filepath, 'rb') as f:
            header = f.read(16)
            cypher_text = f.read()
        data = self._decrypt(cypher_text)
        decrypted_header = data[:16]
        self._validate_header(header, decrypted_header)
        plain_text = str(data[16:], 'utf-8')
        cds = json.loads(plain_text, cls=ClientDataDecoder)
        if cds is None:
            cds = []
        return cds

    def save(self, filepath, client_data_list, new_passphrase=None):
        """Store ClientData objects into encrypted file.

        Store the list of ClientData objects as a JSON document in a file
        encrypted with the passphrase.

        Args:
            filepath: the fully qualified path to the data file.
            client_data_list: a list of ClientData objects to store in the
                data file.

        """
        import struct

        plain_text = json.dumps(
            client_data_list, sort_keys=True, indent=4, separators=(',', ': '),
            cls=ClientDataEncoder)
        header = b''.join([
            struct.pack("!I", self.__magic_number),
            struct.pack("!I", self.__file_version),
            struct.pack("!I", self.__key_stretches),
            struct.pack("!I", self.__magic_number)])
        data = b''.join([
            header,
            bytes(plain_text, 'utf-8')])
        if new_passphrase is not None:
            self.__key = self._produce_key(new_passphrase)
            self.__iv = self._produce_iv(self.__key)
        cypher_text = self._encrypt(data)
        with open(filepath, 'wb') as f:
            f.write(header)
            f.write(cypher_text)

    def validate(self, filepath):
        """Decrypt the data file header, and validate the file is readable.

        Decrypt the initial part of the file and validate it to ensure the
        passphrase is correct.

        Args:
            filepath: the fully qualified path to the data file.

        Returns:
            True if the decrypted data in the leading section of the file
            matches expected values; otherwise, returns False (meaning
            the phassphrase is invalid, or the number of key stretching hashes
            is invalid, or both are invalid).

        """
        header_bytes = b''
        cypher_bytes = b''
        with open(filepath, 'rb') as f:
            header_bytes = f.read(16)
            cypher_bytes = f.read(16)
        data = self._decrypt(cypher_bytes, strip_padding=False)
        try:
            self._validate_header(header_bytes, data)
        except DecryptionError:
            return False
        return True
