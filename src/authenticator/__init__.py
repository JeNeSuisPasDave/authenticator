# This Source Code Form is subject to the terms of the MIT License.
# If a copy of the MIT License was not distributed with this
# file, you can obtain one at https://opensource.org/licenses/MIT.
#
"""
Copyright (c) 2016 Dave Hein <dhein@acm.org>.

This module provides a HOTP/TOTP passcode generation utility, implementing
RFC4226 and RFC6238. It is useful for one-time passwords used as part of
multi-factor authentication systems.

The iOS app Google Authenticator is an example of another application that
provides a similar function. This software was created as a supplement and
backup for Google Authenticator, one that can be run on general purpose
computers.

"""

from authenticator.cli import CLI
from authenticator.cli import DuplicateKeyError
from authenticator.data import ClientData
from authenticator.data import ClientDataDecoder
from authenticator.data import ClientDataEncoder
from authenticator.data import ClientFile
from authenticator.data import DecryptionError
from authenticator.data import FileCorruptionError
from authenticator.hotp import HOTP

# These next lines just eliminate linter warnings
#
x = CLI.__class__
x = DuplicateKeyError.__class__
x = ClientData.__class__
x = ClientDataDecoder.__class__
x = ClientDataEncoder.__class__
x = ClientFile.__class__
x = DecryptionError.__class__
x = FileCorruptionError.__class__
x = HOTP.__class__

__author__ = "Dave Hein <dhein@acm.org>"
__license__ = "MIT"
__version__ = "1.1.3"
