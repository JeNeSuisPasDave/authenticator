# This Source Code Form is subject to the terms of the MIT License.
# If a copy of the MIT License was not distributed with this
# file, you can obtain one at https://opensource.org/licenses/MIT.
#
"""
The command line interface for the authenticator application.

This implementation requires:

    * Python 3.5 or later
    * cryptography 1.3 or later (see https://cryptography.io/en/latest/)
    * python-dateutil 2.1 or later
        (see https://pypi.python.org/pypi/python-dateutil/2.1)
    * six 1.10 or later (https://pypi.python.org/pypi/six/1.10.0)

"""

import sys
from authenticator.data import ClientData, ClientFile
from authenticator.hotp import HOTP


class DuplicateKeyError(KeyError):
    """Object with same key already exists in the collection."""

    pass


class CLI:
    """Command Line Interface."""

    class RedirectStdStreams:
        """A context manager temporarily redirects the standard streams."""

        def __init__(self, stdout=None, stderr=None):
            self._stdout = stdout or sys.stdout
            self._stderr = stderr or sys.stderr

        def __enter__(self):
            self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
            self.old_stdout.flush()
            self.old_stderr.flush()
            sys.stdout, sys.stderr = self._stdout, self._stderr

        def __exit__(self, exc_type, exc_value, traceback):
            self._stdout.flush()
            self._stderr.flush()
            sys.stdout = self.old_stdout
            sys.stderr = self.old_stderr

    def __init__(self, stdin=None, stdout=None, stderr=None):
        """Constructor."""
        import os.path
        import argparse
        import textwrap

        self.__iso_fmt = "%Y%m%dT%H%M%S%z"
        self.__std_fmt = "%Y-%m-%d %H:%M:%S %z"
        self.__stdin_redirected = False
        if stdin is not None:
            self.__stdin = stdin
            self.__stdin_redirected = True
        else:
            self.__stdin = sys.stdin
        self.__stdout_redirected = False
        if stdout is not None:
            self.__stdout = stdout
            self.__stdout_redirected = True
        else:
            self.__stdout = sys.stdout
        self.__stderr_redirected = False
        if stderr is not None:
            self.__stderr = stderr
            self.__stderr_redirected = True
        else:
            self.__stderr = sys.stderr
        self.__passphrase = None
        self.__new_passphrase = None
        self.__shared_secret = None
        self.__data_dir = self._locate_data_dir()
        self.__data_file = os.path.join(self.__data_dir, 'authenticator.data')
        self.__cf = None
        self.__re_client_id_pattern = None
        self.__raw_client_id_pattern = None
        self.__abandon_cli = False

        epilog_width = 78
        epilog1 = textwrap.fill(textwrap.dedent(
            """
            By default the clientIdPattern is a wildcard string. The '*'
            character represents zero or more other characters. A string
            without any '*' characters is treated as if there were a '*' at
            the beginning and end (so that specifying 'abc' is the same as
            specifying '*abc*').""").strip(), width=epilog_width)
        epilog2 = textwrap.fill(textwrap.dedent(
            """
            If the '--regex' option is used then the clientIdPattern is
            interpreted as a Python regular expression. See
            http://docs.python.org/3.3/howto/regex.html for documentation on
            Python regular expressions.""").strip(), width=epilog_width)
        epilog = "\n".join([epilog1, "\n", epilog2])
        epilog3 = textwrap.fill(textwrap.dedent(
            """
            Both the 'oldClientId' and 'newClientId' arguments are exact
            strings. They are not wildcard or regular expression patterns.
            Only one HOTP/TOTP configuration can be renamed at a time."""
            ).strip(),
            width=epilog_width)

        # main command
        #
        self.parser = argparse.ArgumentParser(
            description="Run or manage HOTP/TOTP calculations",
            prog='authenticator')
        self.parser.add_argument(
            '--version', dest='showVersion', action='store_true',
            default=False, help="show the software version")
        self.parser.add_argument(
            '--data', dest='altDataFile', action='store',
            help="Specify the path to an alternate data file")
        subparsers = self.parser.add_subparsers(
            title="Sub-commands", description="\nValid Sub-Commands",
            help="\nSub-command Help")

        # sub-command: add
        #
        sp_add = subparsers.add_parser(
            'add',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            help="add a HOTP/TOTP configuration",
            description=textwrap.fill(
                "Add a new HOTP/TOTP configuration to the data file.",
                width=epilog_width))
        sp_add.add_argument(
            'clientIdToAdd', action='store',
            help="a unique identifier for the HOTP/TOTP configuration")
        sp_add.add_argument(
            '--counter', type=int, dest='counter', action='store',
            help="initial counter value for a counter-based" +
            " HOTP calculation (no default)")
        sp_add.add_argument(
            '--length', type=int, dest='passwordLength', action='store',
            help="length of the generated password (default: 6)")
        sp_add.add_argument(
            '--period', type=int, dest='period', action='store',
            help="length of the time period in seconds for a time-based" +
            " HOTP calculation (default: 30)")
        sp_add.set_defaults(subcmd='add')

        # sub-command: delete
        #
        sp_del = subparsers.add_parser(
            'delete', aliases=['del'],
            formatter_class=argparse.RawDescriptionHelpFormatter,
            help="delete a HOTP/TOTP configuration",
            epilog=epilog,
            description=textwrap.fill(
                "Delete one or more HOTP/TOTP configurations from " +
                "the data file.",
                width=epilog_width))
        sp_del.add_argument(
            'clientIdPattern', action='store',
            help="wildcard pattern to match the client IDs of one or " +
            "more HOTP/TOTP configurations")
        sp_del.add_argument(
            '-e', '--regex', dest='patternIsRegex', action='store_true',
            default=False, help="clientIdPattern is a regular expression")
        sp_del.add_argument(
            '-q', '--quiet', dest='quiet', action='store_true', default=False,
            help="Do not ask for confirmation")
        sp_del.set_defaults(subcmd='delete')

        # sub-command: generate
        #
        sp_gen = subparsers.add_parser(
            'generate', aliases=['gen'],
            formatter_class=argparse.RawDescriptionHelpFormatter,
            help="generate passwords for one or more HOTP/TOTP configurations",
            epilog=epilog,
            description=textwrap.fill(
                "Generate passwords for one or more HOTP/TOTP " +
                "configurations from the data file.",
                width=epilog_width))
        sp_gen.add_argument(
            'clientIdPattern', action='store', nargs='?', default='',
            help="wildcard pattern to match the client IDs of one or " +
            "more HOTP/TOTP configurations")
        sp_gen.add_argument(
            '-e', '--regex', dest='patternIsRegex', action='store_true',
            default=False, help="client_id_pattern is a regular expression")
        sp_gen.add_argument(
            '--refresh', dest='refresh', action='store', default='5',
            help="specify when the time-based passwords are recalcuated." +
            " Can be a period in seconds, or 'expiration' to recalculate" +
            " when any of the periods expire, or 'once' to do it once." +
            " (default: 5 seconds; always 'once' for counter-based" +
            " configurations)")
        sp_gen.add_argument(
            '-c', '--counter-based', dest='includeCounterBasedConfigs',
            action='store_true', default=False,
            help="generate passwords for counter-based HOTP/TOTP" +
            " configurations (which are skipped by default).")
        sp_gen.set_defaults(subcmd='generate')

        # sub-command: info
        #
        sp_info = subparsers.add_parser(
            'info', help="show information about this software and your data",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.fill(
                "Show software version information, support information, " +
                "source code location, et cetera. Also show the location " +
                "of the data file and when it was last modified.",
                width=epilog_width))
        sp_info.set_defaults(subcmd='info')

        # sub-command: list
        #
        sp_list = subparsers.add_parser(
            'list', help="list HOTP/TOTP configurations",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=epilog,
            description=textwrap.fill(
                "List one or more HOTP/TOTP configurations from the " +
                "data file.",
                width=epilog_width))
        sp_list.add_argument(
            'clientIdPattern', action='store', nargs='?', default='',
            help="wildcard pattern to match the client IDs of one or " +
            "more HOTP/TOTP configurations")
        sp_list.add_argument(
            '-e', '--regex', dest='patternIsRegex', action='store_true',
            default=False, help="client_id_pattern is a regular expression")
        sp_list.add_argument(
            '-v', '--verbose', dest='verbose', action='count',
            default=0,
            help="Show all properties of each configuration; -vv to show more")
        sp_list.set_defaults(subcmd='list')

        # sub-command: set
        #
        sp_set = subparsers.add_parser(
            'set', help="set HOPT configuration values",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=textwrap.fill(
                "Set configuration values for one or more HOTP " +
                "configurations from the data file. NOTE: this feature " +
                "is not implemented.",
                width=epilog_width))
        setsubparsers = sp_set.add_subparsers(
            title="set commands", description="\nValid set commands",
            help="\nset command help")
        sp_set_passphrase = setsubparsers.add_parser(
            'passphrase',
            help="Change the passphrase",
            description=textwrap.fill(
                "Change the passphrase for the data file.",
                width=epilog_width))
        sp_set_passphrase.set_defaults(subsubcmd='passphrase')
        sp_set_rename = setsubparsers.add_parser(
            'clientid',
            help="Rename a HOTP/TOTP configuration",
            epilog=epilog3,
            description=textwrap.fill(
                "Change the client ID for a HOTP/TOTP configuration.",
                width=epilog_width))
        sp_set_rename.add_argument(
            dest='oldClientId', action='store',
            help="client ID of HOTP/TOTP configuration to be renamed")
        sp_set_rename.add_argument(
            dest='newClientId', action='store',
            help="new client ID to be assigned to the HOTP/TOTP configuration")
        sp_set_rename.set_defaults(subsubcmd='clientid')
        sp_set.set_defaults(subcmd='set')

    # -------------------------------------------------------------------------+
    # internal methods
    # -------------------------------------------------------------------------+

    def _add_client_data_to_file(self, cd_new):
        """Add the ClientData object to the file.

        Args:
            cd_new: the ClientData object to add to the file.

        Raises:
            DuplicateKeyError: There already exists a ClientData object with
                the same client_id in the data file.
        """
        import datetime

        cds_existing = self.__cf.load(self.__data_file)
        for cd_existing in cds_existing:
            if cd_new.client_id() == cd_existing.client_id():
                raise DuplicateKeyError("That configuration already exists.")
        cds_new = cds_existing[:]
        now = datetime.datetime.now(ClientData.tz())
        if not cd_new.counter_from_time():
            cd_new.set_last_count_update_time(now.strftime(self.__iso_fmt))
        cds_new.append(cd_new)
        self.__cf.save(self.__data_file, cds_new)

    def _apply_alt_data_file_path(self, alt_data_file):
        """Convert the alt_data_file argument to a valid dataDir and dataFile.

        Args:
            alt_data_file: the data file or data dir path passed in on the
                command line

        Returns:
            True if everything is OK; False if there was some kind of error.

        """
        import os.path
        import os

        if alt_data_file is None:
            return False
        adf_is_directory = False
        # If it ends with '/' then assume it is a directory.
        #
        if alt_data_file.endswith(os.sep):
            adf_is_directory = True
        # Expand the user mnemonic
        #
        path = os.path.expanduser(alt_data_file)
        # If relative, then expand it
        #
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        # Check to see if it exists. If it does, is it a directory
        # or a file?
        if os.path.exists(path):
            if os.path.isdir(path):
                adf_is_directory = True
        # Assign the dataDir and dataFile
        #
        if adf_is_directory:
            self.__data_dir = path
            self.__data_file = os.path.join(
                self.__data_dir, 'authenticator.data')
        else:
            self.__data_dir = os.path.dirname(path)
            self.__data_file = path
        # Get out
        #
        if not os.path.exists(self.__data_dir):
            return False
        return True

    def _capture_passphrase(self, is_new=False):
        """Ask the user to supply and confirm the new passphrase.

        Hitting enter at the new passphrase prompt will terminate the
        capture without any passphrase.

        Args:
            is_new: True if capturing a replacement passphrase; otherwise,
                capturing the initial passphrase.
        """
        import getpass

        infix_prompt = "new " if is_new else ""
        pp1 = None
        pp2 = None
        first_time = True
        while (pp1 is None or
                pp2 is None or
                pp1 != pp2):
            if not first_time:
                print(
                    "Passphrases do not match. Try again.",
                    file=self.__stdout)
            first_time = False
            # Prompt for new passphrase
            #
            if (self._stdin_is_tty() and
                    sys.stdin is self.__stdin):
                pp1 = getpass.getpass(
                    "Enter {0}passphrase: ".format(infix_prompt),
                    stream=self.__stdout)
            else:
                print(
                    "Enter {0}passphrase: ".format(infix_prompt),
                    end="", flush=True, file=self.__stdout)
                pp1 = self.__stdin.readline()
            pp1 = pp1.strip()
            # If no passphrase, then get  out
            #
            if 0 == len(pp1):
                self.__abandon_cli = True
                return
            # Prompt to confirm passphrase
            #
            if (self._stdin_is_tty() and
                    sys.stdin is self.__stdin):
                pp2 = getpass.getpass(
                    "Confirm {0}passphrase: ".format(infix_prompt),
                    stream=self.__stdout)
            else:
                print(
                    "Confirm {0}passphrase: ".format(infix_prompt),
                    end="", flush=True, file=self.__stdout)
                pp2 = self.__stdin.readline()
            pp2 = pp2.strip()
            # If no passphrase, then get  out
            #
            if 0 == len(pp2):
                self.__abandon_cli = True
                return
        # We have matching passphrases
        #
        if is_new:
            self.__new_passphrase = pp1
        else:
            self.__passphrase = pp1

    def _confirm_delete(self, client_id):
        rc = self._query_prompt(
            "Delete {0}?".format(client_id), default_value_index=1)
        if 'yes' == rc:
            return True
        return False

    def _delete_client_data_from_file(self, id_pattern='*'):
        """Delete ClientData from the data file.

        Args:
            id_pattern: A wildcard pattern to match the client ID

        Returns:
            The count of deleted configurations.

        """
        deleted_count = 0
        # Load the ClientData objects
        #
        cds = self.__cf.load(self.__data_file)
        # Which of them should be delete
        #
        cds_to_delete = list(
            filter(lambda x: self._match_clientid(x, id_pattern), cds))
        if 0 == len(cds_to_delete):
            # No change, so no need to save the file; just get out
            return deleted_count
        # Collect just the client IDs of the ClientData objects to
        # be deleted
        #
        client_ids_to_delete = [
            cd_to_delete.client_id() for cd_to_delete in cds_to_delete]
        # Confirm each delete, if not quiet
        #
        if not self.args.quiet:
            provisional_client_ids = list(
                filter(
                    lambda x:
                    self._confirm_delete(x), client_ids_to_delete))
            client_ids_to_delete = provisional_client_ids

        # Assemble the list of ClientData objects to keep
        #
        cds_to_keep = list(
            filter(lambda x: x.client_id() not in client_ids_to_delete, cds))
        deleted_count = len(cds) - len(cds_to_keep)
        # Update the file
        #
        if 0 < deleted_count:
            self.__cf.save(self.__data_file, cds_to_keep)
        # Get out
        #
        return deleted_count

    def _escape_for_re(self, clear_text):
        """Convert a wildcard string to an regex.

        Convert a wildcard string to a regular expression string,
        escaping all the regular expression special characters.

        Args:
            clear_text: a wildcard string. Any '*' will get converted to
            '.*' patterns in the regular expression; all other characters
            will match exactly.

        Returns:
            A regular expression pattern that matches the intent of the
            clear_text wildcard search string. If input is None or an empty
            string, then '.*' is the result.

        """
        # Input validation
        #
        if clear_text is None:
            return '^.*$'
        wc_text = clear_text.strip()
        if 0 == len(wc_text):
            return '^.*$'

        re_text = ['^']
        for c in wc_text:
            if '*' == c:
                re_text.append('.*')
            elif c in ('.', '^', '$', '+', '?', '\\', '|', '{', '(', '['):
                re_text.append("\\{0}".format(c))
            else:
                re_text.append(c)
        re_text.append('$')
        return "".join(re_text)

    def _generate_once(self, cds_to_calc):
        """Generate a HOTP for each configuration in cds_to_calc.

        Args:
            cds_to_calc: A list of ClientData objects for which HOTP
            calculations should be performed and the results printed
            to stdout.

        Returns:
            The smallest secondsRemaining of all the time-based HOTPs
            that were calculated; None if no time-based HOTPs were in
            cds_to_calc.

        """
        expiration_guard = 10**6
        most_recent_expiration = expiration_guard  # pretty big
        for cd in cds_to_calc:
            if cd.counter_from_time():
                hotp = HOTP()
                code_string, remaining_seconds = hotp.generate_code_from_time(
                    cd.shared_secret(),
                    code_length=cd.password_length(),
                    period=cd.period())
                if remaining_seconds < most_recent_expiration:
                    most_recent_expiration = remaining_seconds
                print(
                    "{0}: {1} (expires in {2} seconds)".format(
                        cd.client_id(), code_string, remaining_seconds),
                    file=self.__stdout)
            elif self.args.includeCounterBasedConfigs:
                hotp = HOTP()
                code_string = hotp.generate_code_from_counter(
                    cd.shared_secret(),
                    cd.incremented_count(),
                    code_length=cd.password_length())
                self._update_client_in_data_file(cd)
                print(
                    "{0}: {1} (for count {2})".format(
                        cd.client_id(), code_string, cd.last_count()),
                    file=self.__stdout)
        # Get out
        #
        if expiration_guard == most_recent_expiration:
            return None
        else:
            return most_recent_expiration

    def _generate(self, id_pattern='*', refresh=5):
        """Generate and display the HOTP codes for the matching configurations.

        Args:
            id_pattern: A wildcard pattern to match the client ID
            refresh: One of 'once' (calculate once), 'expiration' (calculate
                again when the code expires, or an integer number of seconds
                for the interval to repeat the calculation. This is ignored
                for counter-based HOTP configurations, which are only
                calculated once.
        """
        import time

        # Load the ClientData objects
        #
        cds = self.__cf.load(self.__data_file)
        # Which of them should be calculated
        #
        cds_to_calc = list(
            filter(lambda x: self._match_clientid(x, id_pattern), cds))
        if 0 == len(cds_to_calc):
            # None found; just get out
            print("No HOTP/TOTP configurations found.", file=self.__stdout)
            return
        # Calculate the HOTPs
        first_time = True
        keep_going = True
        while keep_going:
            if not first_time:
                print("", file=self.__stdout)
            first_time = False
            soonest_expiration = self._generate_once(cds_to_calc)
            if soonest_expiration is None:
                # we only calculate counter-based HOTPs once
                keep_going = False
            elif 'once' == self.args.refresh:
                keep_going = False
            elif 'expiration' == self.args.refresh:
                time.sleep(soonest_expiration)
            else:
                time.sleep(self.args.refresh)

    def _list_client_data_verbose(self, cd):
        """Verbose display of one ClientData object."""
        import base64
        import iso8601

        print("id: {0}".format(cd.client_id()), file=self.__stdout)
        if (1 < self.args.verbose):
            ss = cd.shared_secret()
            if type(b'AB') == type(ss):
                print("secret: {0}".format(base64.base32encode(ss)))
            else:
                print("secret: {0}".format(ss))
        if cd.counter_from_time():
            print(
                "time-based; period: {0}".format(cd.period()),
                file=self.__stdout)
        else:
            print(
                "counter-based; last counter: {0}".format(
                    cd.last_count()),
                file=self.__stdout)
            t = iso8601.parse_date(cd.last_count_update_time())
            print(
                "count updated: {0}".format(
                    t.strftime(self.__std_fmt)),
                file=self.__stdout)
        print(
            "password length: {0}".format(cd.password_length()),
            file=self.__stdout)
        if 0 < len(cd.tags()):
            print(
                "tags: {0}".format(", ".join(cd.tags())),
                file=self.__stdout)
        if 0 < len(cd.note()):
            print(
                "note: {0}".format(", ".join(cd.note())),
                file=self.__stdout)

    def _list_client_data(self, id_pattern='*'):
        """Display the ClientData objects for all configurations."""
        # TODO: [DTH] add wild card filtering

        cds = self.__cf.load(self.__data_file)
        cds_to_list = list(
            filter(lambda x: self._match_clientid(x, id_pattern), cds))
        if 0 == len(cds_to_list):
            print("No HOTP/TOTP configurations found.", file=self.__stdout)
        first_time = True
        for cd in cds_to_list:
            if first_time:
                # add a blank line to separate list from passphrase prompt
                print("", file=self.__stdout)
            if 0 < self.args.verbose:
                if not first_time:
                    # add a blank line between clients
                    print("", file=self.__stdout)
                self._list_client_data_verbose(cd)
            else:
                print("{0}".format(cd.client_id()), file=self.__stdout)
            first_time = False

    def _locate_data_dir(self):
        """Find the default location of the data file.

        On Windows, this is "%HOMEDRIVE%%HOMEPATH%/.authenticator/".

        On OS X (Mac), this is "~/.authenticator/".

        On other Unix systems, this is "~/.authenticator/".
        """
        import os
        import os.path

        root_seed = "~"
        root = os.path.expanduser(root_seed)
        root = os.path.join(root, ".authenticator")
        if root_seed == root:
            raise SystemExit("Could not expand the path '~/.authenticator'")
        if not os.path.exists(root):
            os.mkdir(root, mode=0o755)
        return root

    def _make_client_data(self):
        cd_args = {
            'clientId': self.args.clientIdToAdd,
            'sharedSecret': self.__shared_secret
            }
        if self.args.counter is not None:
            cd_args['counterFromTime'] = False
            cd_args['lastCount'] = self.args.counter
        elif self.args.period is not None:
            cd_args['period'] = self.args.period
        if self.args.passwordLength is not None:
            cd_args['passwordLength'] = self.args.passwordLength
        cd = ClientData(**cd_args)
        return cd

    def _match_clientid(self, cd, pattern='*'):
        """Whether a ClientData.client_id() matches the pattern.

        Args:
            cd: A ClientData object to match.
            pattern: The wildcard pattern used to match the client ID.

        Returns:
            True if the cd.client_id() matches the pattern; otherwise, False.

        """
        import re

        if '*' == pattern:
            return True
        if pattern != self.__raw_client_id_pattern:
            self.__raw_client_id_pattern = pattern
            if '*' not in pattern:
                expression = self._escape_for_re("*{0}*".format(pattern))
            else:
                expression = self._escape_for_re(pattern)
            self.__re_client_id_pattern = re.compile(expression)
        if self.__re_client_id_pattern.match(cd.client_id()) is not None:
            return True
        return False

    def _modify_client_data(self, old_cd, **kw_args):
        """Clone ClientData object, adjusting some properties.

        Produce a new ClientData object that is a copy of old_cd,
        changing one or more of the properties.

        Args:
            old_cd: The ClientData object to be copied and modified.
            kw_args:
                A collection of keyword arguments in which the keyword is
                the ClientData property to modify and the value is the new
                property value.

        Returns:
            A new ClientData object with updated properties.

        """
        cd_args = {
            'clientId': old_cd.client_id(),
            'sharedSecret': old_cd.shared_secret(),
            'counterFromTime': old_cd.counter_from_time(),
            'lastCount': old_cd.last_count(),
            'lastCountUpdateTime': old_cd.last_count_update_time(),
            'period': old_cd.period(),
            'passwordLength': old_cd.password_length(),
            'tags': old_cd.tags(),
            'note': old_cd.note()
        }
        for kw in kw_args:
            if kw in cd_args:
                cd_args[kw] = kw_args[kw]
        cd = ClientData(**cd_args)
        return cd

    def _query_passphrase(self):
        """Prompt for passphrase, check against data file.

        Ask the user to supply the passphrase, and confirm it matches
        the data file.

        """
        import getpass

        pp = None
        first_time = True
        while self.__passphrase is None:
            if not first_time:
                print(
                    "Passphrase is incorrect. Try again.",
                    file=self.__stdout)
            # Capture the passphrase
            #
            first_time = False
            if (self._stdin_is_tty() and
                    sys.stdin is self.__stdin):
                pp = getpass.getpass(
                    "Enter passphrase: ", stream=self.__stdout)
            else:
                print(
                    "Enter passphrase: ",
                    end="", flush=True, file=self.__stdout)
                pp = self.__stdin.readline().strip()
            pp = pp.strip()
            # If no passphrase, then get out
            #
            if 0 == len(pp):
                self.__abandon_cli = True
                return
            # Verify the passphrase
            #
            cf = ClientFile(pp)
            if cf.validate(self.__data_file):
                self.__passphrase = pp
                self.__cf = cf

    def _query_shared_secret(self):
        while self.__shared_secret is None:
            print(
                "Enter shared secret: ",
                end="", flush=True, file=self.__stdout)
            ss = self.__stdin.readline().strip()
            if 0 == len(ss):
                self.__abandon_cli = True
                return
            # remote whitespace and make uppercase
            ss = "".join(ss.split()).upper()
            hotp = HOTP()
            try:
                hotp.convert_base32_secret_key(ss)
            except Exception as e:
                print(
                    "Invalid shared secret string. {0}.".format(e),
                    file=self.__stdout)
                continue
            self.__shared_secret = ss

    def _query_prompt(
            self,
            prompt_statement, possible_values=('yes', 'no'),
            default_value_index=0):
        """Prompt for a response, but fall back to default.

        Prompt the user for one of a few possible responses, or to accept
        the default response.

        Returns:
            The entered string, or the default string.

        """
        prompt = "{0} ({1}) [{2}]: ".format(
            prompt_statement, "|".join(possible_values),
            possible_values[default_value_index])
        print(prompt, end="", flush=True, file=self.__stdout)
        r = self.__stdin.readline().strip()
        if 0 == len(r):
            r = possible_values[default_value_index]
        while r not in possible_values:
            print(
                "Bad input. Please respond with one of: {0}".format(
                    ", ".join(possible_values)),
                file=self.__stdout)
            print(prompt, end="", flush=True, file=self.__stdout)
            r = self.__stdin.readline().strip()

            if 0 == len(r):
                r = possible_values[default_value_index]
        return r

    def _rewrite_data(self):
        """Rewrite the data file with the new passphrase.

        Raises:
            AssertionError: There is not a new passphrase.
        """
        if self.__new_passphrase is None:
            raise AssertionError("No new passphrase; nothing to do")
        cds = self.__cf.load(self.__data_file)
        self.__cf.save(self.__data_file, cds, self.__new_passphrase)

    def _rename_client_id(self, old_client_id, new_client_id):
        """Change the client id for an existing HOTP configuration.

        Returns:
            True if the rename was performed; False if there was no change
            made.

        """
        import re

        cds_old = self.__cf.load(self.__data_file)
        cds_new = []
        expression = self._escape_for_re(old_client_id)
        re_old_client_id = re.compile(expression)
        found_id = False
        for cd in cds_old:
            if re_old_client_id.match(cd.client_id()) is not None:
                found_id = True
                cd_new = self._modify_client_data(cd, clientId=new_client_id)
                cds_new.append(cd_new)
            else:
                cds_new.append(cd)
        if not found_id:
            print(
                "No configuration found with client ID '{0}'".format(
                    old_client_id), file=self.__stderr)
            return False
        self.__cf.save(self.__data_file, cds_new)
        return True

    def _show_info(self):
        """Show 'about' information for this software.

        Show software version information, support information, source
        code location, et cetera.

        Also show the location of the data file and when it was last modified.

        """
        import textwrap
        import authenticator

        print("authenticator version {0}".format(
            authenticator.__version__), file=self.__stdout)
        print("Copyright (c) 2016 David T. Hein.", file=self.__stdout)
        print(
            "MIT License. See https://opensource.org/licenses/MIT",
            file=self.__stdout)
        print(
            "\nData file location: {0}".format(self.__data_file),
            file=self.__stdout)
        addendum = textwrap.fill(textwrap.dedent(
            """
            See https://github.com/jenesuispasdave/github/ for the source code
            repository, the latest version, and technical support.""").strip(),
            width=78)
        print("\n{0}".format(addendum), file=self.__stdout)

    def _show_version(self):
        """Show the version only.

        Not as verbose as 'authenticator info'.

        """
        import authenticator

        print("authenticator version {0}".format(
            authenticator.__version__), file=self.__stdout)

    def _stdin_is_tty(self):
        """Detect whether the stdin is mapped to a terminal console.

        I found this technique in the answer by thg435 here:
        http://stackoverflow.com/questions/13442574/how-do-i-determine-if-sys-stdin-is-redirected-from-a-file-vs-piped-from-another

        """
        import os
        import stat

        mode = os.fstat(0).st_mode
        if ((not stat.S_ISFIFO(mode)) and  # piped
                (not stat.S_ISREG(mode))):  # redirected
            return True
        else:
            # not piped or redirected, so assume terminal input
            return False

    def _update_client_in_data_file(self, cd):
        changed = False
        cds = self.__cf.load(self.__data_file)
        for i in range(0, len(cds)):
            if cd.client_id() == cds[i].client_id():
                cds[i] = cd
                changed = True
        if changed:
            self.__cf.save(self.__data_file, cds)

    def _validate_args_add(self):
        """Validate the arguments for the CLI subcommand add."""
        if (self.args.counter is not None and
                self.args.period is not None):
            self.parser.error(
                "--counter and --period are mutually exclusive")

    def _validate_args_generate(self):
        """Validate the arguments for the CLI subcommand generate."""
        try:
            x = int(self.args.refresh)
            self.args.refresh = x
        except ValueError:
            if self.args.refresh not in ('once', 'expiration'):
                self.parser.error(
                    "--refresh requires an integer number of seconds," +
                    " or 'once', or 'expiration'")

    def _validate_args_set(self):
        """Validate the arguments for the CLI subcommand set."""
        if 'clientid' == self.args.subsubcmd:
            if '*' in self.args.oldClientId:
                self.parser.error(
                    "oldClientId must be an exact match; no wildcards")
            if '*' in self.args.newClientId:
                self.parser.error(
                    "newClientId must not be a wildcard string")

    def _validate_args_missing_subcmd(self):
        """Validate the arguments for the CLI if no subcmd."""
        if 'alt_data_file' in dir(self.args):
            self.parser.error(
                "missing subcommand (choose from 'add', 'delete', " +
                "'del', 'generate', 'gen', 'info', 'list', 'set')")

    def _validate_args_data_file(self):
        """Validate the data_file argument for the CLI."""
        if not self._apply_alt_data_file_path(self.args.altDataFile):
            self.parser.error(
                "The directory for the data file does not exist.")

    def _validate_args(self):
        """Validate command line arguments."""
        # if '--version' specified, ignore remainder of command line
        #
        if self.args.showVersion:
            if 'subcmd' in dir(self.args):
                self.args.subcmd = None
                return

        # if '--data' specified, update the data file and data dir paths
        #
        if self.args.altDataFile is not None:
            self._validate_args_data_file()
        # check subcommands and arguments
        #
        if 'subcmd' not in dir(self.args):
            self._validate_args_missing_subcmd()
            return

        if 'del' == self.args.subcmd:
            self.args.subcmd = 'delete'
        elif 'gen' == self.args.subcmd:
            self.args.subcmd = 'generate'

        if 'add' == self.args.subcmd:
            self._validate_args_add()
        elif 'generate' == self.args.subcmd:
            self._validate_args_generate()
        elif 'set' == self.args.subcmd:
            self._validate_args_set()

    # -------------------------------------------------------------------------+
    # public methods
    # -------------------------------------------------------------------------+

    def create_data_file(self):
        """Create the data file if it does not yet exist.

        Will offer to create the data file. If offer is declined, then exit.
        Otherwise accept and confirm the passphrase.

        """
        import os.path

        if self.__abandon_cli:
            return
        if 'subcmd' not in dir(self.args):
            return
        if 'info' == self.args.subcmd:
            return

        # If the data file exists, then there is nothing to do here so just
        # get out.
        #
        if os.path.exists(self.__data_file):
            return

        # If the data file does not exist, and the subcommand was not 'add',
        # then report no dataset found and get out.
        if 'add' != self.args.subcmd:
            print(
                "No data file was found; cannot complete request.",
                file=self.__stdout)
            self.__abandon_cli = True
            return

        # Otherwise, offer the opportunity to create the data file
        #
        prompt = (
            "No data file was found." +
            " Do you want to create your data file?")
        r = self._query_prompt(prompt)
        if ('yes' == r):
            self._capture_passphrase()
            if self.__passphrase is not None:
                self.__cf = ClientFile(self.__passphrase)
                self.__cf.save(self.__data_file, [])
        else:
            self.__abandon_cli = True

    def parse_command_args(self, args):
        """Parse the command line arguments."""
        if self.__abandon_cli:
            return

        if (self.__stdout_redirected and
                self.__stderr_redirected):
            with CLI.RedirectStdStreams(
                    stdout=self.__stdout, stderr=self.__stderr):
                self.args = self.parser.parse_args(args)
                self._validate_args()
        else:
            self.args = self.parser.parse_args(args)
            self._validate_args()

    def prompt_for_secrets(self):
        """Prompt for passphrase and, if an 'add', the shared secret."""
        if self.__abandon_cli:
            return
        if 'subcmd' not in dir(self.args):
            return

        # Get the passphrase, if needed for this subcommand
        #
        if self.args.subcmd in (
                'add', 'delete', 'generate', 'list', 'set'):
            self._query_passphrase()
            if self.__passphrase is None:
                return

        # Get the new passphrase, if changing the passphrase
        #
        if (('set' == self.args.subcmd) and
                ('passphrase' == self.args.subsubcmd)):
            self._capture_passphrase(True)
            if self.__new_passphrase is None:
                return

        # Get the shared secret, if needed for this subcommand
        #
        if 'add' == self.args.subcmd:
            self._query_shared_secret()

    def _execute_add(self):
        """Execute the add action."""
        cd = self._make_client_data()
        try:
            self._add_client_data_to_file(cd)
        except DuplicateKeyError:
            print(
                "Add failed. That configuration already exists.",
                file=self.__stdout)
            return
        print("OK", file=self.__stdout)

    def _execute_delete(self):
        """Execute the delete action."""
        delete_count = self._delete_client_data_from_file(
            self.args.clientIdPattern)
        if 0 == delete_count:
            print("No configurations deleted.", file=self.__stdout)
        elif 1 == delete_count:
            print("Deleted 1 configuration.", file=self.__stdout)
        else:
            print(
                "Deleted {0} configurations.".format(delete_count),
                file=self.__stdout)

    def _execute_generate(self):
        """Execute the geneater action."""
        self._generate(self.args.clientIdPattern, self.args.refresh)

    def _execute_list(self):
        """Execute the list action."""
        self._list_client_data(self.args.clientIdPattern)

    def _execute_set(self):
        """Execute the set action."""
        if 'passphrase' == self.args.subsubcmd:
            self._rewrite_data()
            print("OK", file=self.__stdout)
        if 'clientid' == self.args.subsubcmd:
            change_made = self._rename_client_id(
                self.args.oldClientId, self.args.newClientId)
            if change_made:
                print("OK", file=self.__stdout)
            else:
                print("Nothing changed.", file=self.__stdout)
        else:
            print(
                "'set {0}' is not implemented.".format(
                    self.args.subsubcmd),
                file=self.__stdout)

    def _execute_subcmd(self):
        """Execute the subcmd (that needs file access)."""
        if 'add' == self.args.subcmd:
            self._execute_add()
        elif 'delete' == self.args.subcmd:
            self._execute_delete()
        elif 'generate' == self.args.subcmd:
            self._execute_generate()
        elif 'list' == self.args.subcmd:
            self._execute_list()
        elif 'set' == self.args.subcmd:
            self._execute_set()
        else:
            print(
                "'{0}' is not implemented.".format(self.args.subcmd),
                file=self.__stdout)

    def execute(self):
        """execute the requested actions."""
        if self.__abandon_cli:
            return

        if self.args.showVersion:
            self._show_version()
            return

        if self.args.subcmd not in (
                'add', 'delete', 'generate', 'info', 'list', 'set'):
            print(
                "'{0}' is not implemented.".format(self.args.subcmd),
                file=self.__stdout)
            return

        if 'set' == self.args.subcmd:
            if self.args.subsubcmd not in (
                    'passphrase', 'clientid'):
                print(
                    "'set {0}' is not implemented.".format(
                        self.args.subsubcmd),
                    file=self.__stdout)
                return

        if 'info' == self.args.subcmd:
            self._show_info()
            return

        # The rest of the subcommands need access to the file.
        # If there is no file (because no valid passphrase supplied,
        # for example), then there is nothing to do.
        #
        if self.__cf is None:
            return

        # Execute the subcmd (that needs access to the file)
        #
        self._execute_subcmd()


# -------------------------------------------------------------------------+
# entry points for setuptools
# -------------------------------------------------------------------------+

def authenticator_command():
    """Entry point for command installed by setuptools."""
    try:
        m = CLI()
        m.parse_command_args(sys.argv[1:])
        m.create_data_file()
        m.prompt_for_secrets()
        m.execute()
    except KeyboardInterrupt:
        print("")

# -------------------------------------------------------------------------+
# module's main method
# -------------------------------------------------------------------------+

if '__main__' == __name__:
    try:
        m = CLI()
        m.parse_command_args(sys.argv[1:])
        m.create_data_file()
        m.prompt_for_secrets()
        m.execute()
    except KeyboardInterrupt:
        print("")
