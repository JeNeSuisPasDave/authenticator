# This Source Code Form is subject to the terms of the MIT License.
# If a copy of the MIT License was not distributed with this
# file, you can obtain one at https://opensource.org/licenses/MIT.
#
"""Unit tests for the cli module."""

import unittest
import unittest.mock
import os
import re
import sys
from authenticator import CLI


class CoreCLITests(unittest.TestCase):
    """Tests for the cli module."""

    class RedirectStdStreams:
        """Redirect the standard streams.

        A context manager that can temporarily redirect the standard
        streams.

        """

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

    # NOTE: many of theses tests use a mock for expanduser to change the
    #       default location of the data file to a temporary directory so
    #       that the unit tests do not trash the authenticator.data file of
    #       the user running the tests.
    #
    # NOTE: some of these tests use a mock for _get_key_stretches to force a
    #       much faster key stretch algorithm than is used in the normal
    #       execution mode. This is done so the unit tests are fast and
    #       developers won't be tempted to bypass the (otherwise slow) tests.
    #

    def __init__(self, *args):
        """Constructor."""
        from datetime import datetime, timezone, timedelta

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
        #        dt = ut - lt
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
        self.__tz = timezone(dt)

        self.devnull = open(os.devnull, "w")
        super().__init__(*args)

    def __del__(self):
        """Test fixture destructor."""
        if self.devnull is not None:
            self.devnull.close()
            self.devnull = None

    # ------------------------------------------------------------------------+
    # private methods
    # ------------------------------------------------------------------------+

    def _add_three_hotp_to_file(self, expected_passphrase):
        """Add several HOTP to the data file.

        Add several HOTP to the data file, including a counter-based HOTP
        configuration.

        Used by other unit tests to initialize an empty data file with
        something of use to the test.

        Args:
            expected_passphrase: The passphrase used to protect the data file.

        """
        expected_shared_secret1 = "ABCDEFGHABCDEFGHABCDEFGHGY3TQOJQ"
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, expected_passphrase,
            expected_shared_secret1]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "012345@nom.deplume")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write("OK"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # Add the second configuration
        #
        expected_shared_secret2 = "ABCDEFGHGY3TQOJQGEZDGNBVGY3TQOJQ"
        rw_mock.reset_mock()
        rw_mock.readline.side_effect = [
            expected_passphrase, expected_shared_secret2]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "mickey@prisney.com", "--counter", "11")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write("OK"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # Add the third configuration
        #
        expected_shared_secret3 = "GEZDGNBVGY3TQOJQGEZDGNBVABCDEFGH"
        rw_mock.reset_mock()
        rw_mock.readline.side_effect = [
            expected_passphrase, expected_shared_secret3]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "donald@prisney.com", "--period", "20")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write("OK"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)

    def _add_one_time_based_hotp_to_file(self, expected_passphrase):
        """Add a singled time-based HOTP to the data file.

        Used by other unit tests to initialize an empty data file with
        something of use to the test.

        Args:
            expected_passphrase: The passphrase used to protect the data file.

        """
        expected_shared_secret = "ABCDEFGHABCDEFGHABCDEFGHGY3TQOJQ"
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, expected_passphrase,
            expected_shared_secret]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "012345@nom.deplume")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write("OK"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)

    def _assert_configuration_count_from_file(
            self, expected_passphrase, expected_count):
        """Check count using 'list' subcommand.

        Check the count of configurations in the file by using the 'list'
        subcommand.

        Args:
            expected_passphrase: The passphrase used to protect the data file.
            expected_count: The number of listed configurations.

        """
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("list", )
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        if 0 == expected_count:
            calls = [
                unittest.mock.call.write("No HOTP/TOTP configurations found."),
                unittest.mock.call.write("\n")]
            rw_mock.assert_has_calls(calls)
        else:
            expected_call_count = 2 * expected_count
            # add 2 for leading blank line
            expected_call_count += 2
            self.assertEqual(
                expected_call_count, rw_mock.write.call_count,
                "Expected {0} configurations listed".format(expected_count))

    def _side_effect_expand_user(self, path):
        if not path.startswith("~"):
            return path
        path = path.replace("~", self.temp_dir_path.name)
        return path

    # ------------------------------------------------------------------------+
    # setup, teardown, noop
    # ------------------------------------------------------------------------+

    def setUp(self):
        """Create data used by the test cases."""
        import tempfile

        self.temp_dir_path = tempfile.TemporaryDirectory()
        self.temp_dir_path2 = tempfile.TemporaryDirectory()
        return

    def tearDown(self):
        """Cleanup data used by the test cases."""
        self.temp_dir_path2.cleanup()
        self.temp_dir_path2 = None
        self.temp_dir_path.cleanup()
        self.temp_dir_path = None

    def test_noop(self):
        """Excercise tearDown and setUp methods.

        This test does nothing itself. It is useful to test the tearDown()
        and setUp() methods in isolation (without side effects).

        """
        return

    # ------------------------------------------------------------------------+
    # tests for CLI.parse_command_args()
    # ------------------------------------------------------------------------+

    def test_parse_add_counter_based_hotp(self):
        """Test CLI.parse_command_args().

        Happy path. 'add' subcommand with '--counter' argument.

        """
        cut = CLI()
        args = ("add", "sam@i.am", "--counter", "12321")
        cut.parse_command_args(args)
        self.assertEqual('add', cut.args.subcmd)
        self.assertEqual("sam@i.am", cut.args.clientIdToAdd)
        self.assertEqual(12321, cut.args.counter)
        self.assertIsNone(cut.args.passwordLength)
        self.assertIsNone(cut.args.period)
        self.assertNotIn('clientIdPattern', cut.args)

    def test_parse_add_invalid_args(self):
        """Test CLI.parse_command_args().

        'add' subcommand with a bad option argument.

        """
        args = ("add", "my.client.id", "--period", "20", "-v")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_add_time_based_hotp(self):
        """Test CLI.parse_command_args().

        Happy path. 'add' subcommand with no optional arguments.

        """
        cut = CLI()
        args = ("add", "sam@i.am")
        cut.parse_command_args(args)
        self.assertEqual('add', cut.args.subcmd)
        self.assertEqual("sam@i.am", cut.args.clientIdToAdd)
        self.assertIsNone(cut.args.passwordLength)
        self.assertIsNone(cut.args.period)
        self.assertIsNone(cut.args.counter)
        self.assertNotIn('clientIdPattern', cut.args)

    def test_parse_add_time_based_hotp_with_initial_period_and_counter(self):
        """Test CLI.parse_command_args().

        Bad args. 'add' subcommand with unexpected '--counter' argument.

        """
        rw_mock = unittest.mock.MagicMock()
        cut = CLI(stdout=rw_mock, stderr=rw_mock)
        args = ("add", "sam@i.am", "--period", "20", "--counter", "10")
        with self.assertRaises(SystemExit):
            cut.parse_command_args(args)

    def test_parse_add_time_based_hotp_with_length(self):
        """Test CLI.parse_command_args().

        Happy path. 'add' subcommand with '--length' argument.

        """
        cut = CLI()
        args = ("add", "sam@i.am", "--length", "9")
        cut.parse_command_args(args)
        self.assertEqual('add', cut.args.subcmd)
        self.assertEqual("sam@i.am", cut.args.clientIdToAdd)
        self.assertEqual(9, cut.args.passwordLength)
        self.assertIsNone(cut.args.period)
        self.assertIsNone(cut.args.counter)
        self.assertNotIn('clientIdPattern', cut.args)

    def test_parse_add_time_based_hotp_with_length_period(self):
        """Test CLI.parse_command_args().

        Happy path. 'add' subcommand with '--length' and '--period' arguments.

        """
        cut = CLI()
        args = ("add", "sam@i.am", "--period", "17", "--length", "8")
        cut.parse_command_args(args)
        self.assertEqual('add', cut.args.subcmd)
        self.assertEqual("sam@i.am", cut.args.clientIdToAdd)
        self.assertEqual(8, cut.args.passwordLength)
        self.assertEqual(17, cut.args.period)
        self.assertIsNone(cut.args.counter)
        self.assertNotIn('clientIdPattern', cut.args)

    def test_parse_add_time_based_hotp_with_period(self):
        """Test CLI.parse_command_args().

        Happy path. 'add' subcommand with '--period' argument.

        """
        cut = CLI()
        args = ("add", "sam@i.am", "--period", "15")
        cut.parse_command_args(args)
        self.assertEqual('add', cut.args.subcmd)
        self.assertEqual("sam@i.am", cut.args.clientIdToAdd)
        self.assertIsNone(cut.args.passwordLength)
        self.assertEqual(15, cut.args.period)
        self.assertIsNone(cut.args.counter)
        self.assertNotIn('clientIdPattern', cut.args)

    @unittest.mock.patch('os.path.expanduser')
    def test_parse_alt_data_file(self, mock_expanduser):
        """Test CLI.parse_command_args().

        Happy path '--data' argument.

        """
        import os.path
        import os

        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        p = os.path.expanduser("~/Dropball/AppData/authenticator")
        p = os.path.normpath(p)
        os.makedirs(p, mode=0o766)
        alt_path = os.path.normpath(
            "~/Dropball/AppData/authenticator/authenticator.data")
        expected_path = os.path.expanduser(alt_path)
        cut = CLI()
        args = ("--data", alt_path, "info")
        cut.parse_command_args(args)
        self.assertEqual('info', cut.args.subcmd)
        self.assertIn('altDataFile', cut.args)
        self.assertEqual(alt_path, cut.args.altDataFile)
        self.assertEqual(expected_path, cut._CLI__data_file)

    @unittest.mock.patch('os.path.expanduser')
    def test_parse_alt_data_file_missing_dir(self, mock_expanduser):
        """Test CLI.parse_command_args().

        Happy path '--data' argument.

        """
        import os.path
        import os

        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        p = os.path.expanduser("~/Dropball/AppData/authenticator")
        p = os.path.normpath(p)
        alt_path = os.path.normpath(
            "~/Dropball/AppData/authenticator/authenticator.data")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                args = ("--data", alt_path, "info")
                cut.parse_command_args(args)

    @unittest.mock.patch('os.path.expanduser')
    def test_parse_alt_data_dir(self, mock_expanduser):
        """Test CLI.parse_command_args().

        Happy path '--data' argument.

        """
        import os.path
        import os

        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        p = os.path.expanduser("~/Dropball/AppData/authenticator")
        p = os.path.normpath(p)
        os.makedirs(p, mode=0o766)
        alt_path = os.path.normpath("~/Dropball/AppData/authenticator")
        expected_path = os.path.join(
            os.path.expanduser(alt_path), 'authenticator.data')
        cut = CLI()
        args = ("--data", alt_path, "info")
        cut.parse_command_args(args)
        self.assertEqual('info', cut.args.subcmd)
        self.assertIn('altDataFile', cut.args)
        self.assertEqual(alt_path, cut.args.altDataFile)
        self.assertEqual(expected_path, cut._CLI__data_file)

    @unittest.mock.patch('os.path.expanduser')
    def test_parse_alt_data_dir_trailing_slash(self, mock_expanduser):
        """Test CLI.parse_command_args().

        Happy path '--data' argument.

        """
        import os.path
        import os

        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        p = os.path.expanduser("~/Dropball/AppData/authenticator")
        p = os.path.normpath(p)
        os.makedirs(p, mode=0o766)
        alt_path = os.path.normpath("~/Dropball/AppData/authenticator/")
        expected_path = os.path.join(
            os.path.expanduser(alt_path), 'authenticator.data')
        cut = CLI()
        args = ("--data", alt_path, "info")
        cut.parse_command_args(args)
        self.assertEqual('info', cut.args.subcmd)
        self.assertIn('altDataFile', cut.args)
        self.assertEqual(alt_path, cut.args.altDataFile)
        self.assertEqual(expected_path, cut._CLI__data_file)

    def test_parse_del(self):
        """Test CLI.parse_command_args().

        Happy path. 'del' subcommand.

        """
        cut = CLI()
        args = ("del", "sam@i.am")
        cut.parse_command_args(args)
        self.assertEqual('delete', cut.args.subcmd)
        self.assertEqual("sam@i.am", cut.args.clientIdPattern)
        self.assertNotIn('counter', cut.args)
        self.assertNotIn('passwordLength', cut.args)
        self.assertNotIn('period', cut.args)
        self.assertNotIn('clientIdToAdd', cut.args)

    def test_parse_delete(self):
        """Test CLI.parse_command_args().

        Happy path. 'delete' subcommand.

        """
        cut = CLI()
        args = ("delete", "sam@i.am")
        cut.parse_command_args(args)
        self.assertEqual('delete', cut.args.subcmd)
        self.assertEqual("sam@i.am", cut.args.clientIdPattern)
        self.assertNotIn('counter', cut.args)
        self.assertNotIn('passwordLength', cut.args)
        self.assertNotIn('period', cut.args)
        self.assertNotIn('clientIdToAdd', cut.args)

    def test_parse_delete_invalid_args(self):
        """Test CLI.parse_command_args().

        'delete' subcommand with a bad option argument.

        """
        args = ("delete", "my.client.id", "-v")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_delete_missing_client_id_pattern(self):
        """Test CLI.parse_command_args().

        'delete' subcommand with no client id pattern argument.

        """
        args = ("delete")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_gen(self):
        """Test CLI.parse_command_args().

        Happy path. 'gen' subcommand.

        """
        cut = CLI()
        args = ("gen", "sam@i.am")
        cut.parse_command_args(args)
        self.assertEqual('generate', cut.args.subcmd)
        self.assertEqual("sam@i.am", cut.args.clientIdPattern)
        self.assertEqual(5, cut.args.refresh)
        self.assertNotIn('counter', cut.args)
        self.assertNotIn('passwordLength', cut.args)
        self.assertNotIn('period', cut.args)
        self.assertNotIn('clientIdToAdd', cut.args)

    def test_parse_generate(self):
        """Test CLI.parse_command_args().

        Happy path. 'generate' subcommand.

        """
        cut = CLI()
        args = ("gen", "sam@i.am")
        cut.parse_command_args(args)
        self.assertEqual('generate', cut.args.subcmd)
        self.assertEqual("sam@i.am", cut.args.clientIdPattern)
        self.assertEqual(5, cut.args.refresh)
        self.assertNotIn('counter', cut.args)
        self.assertNotIn('passwordLength', cut.args)
        self.assertNotIn('period', cut.args)
        self.assertNotIn('clientIdToAdd', cut.args)

    def test_parse_generate_invalid_args(self):
        """Test CLI.parse_command_args().

        'generate' subcommand with a bad option argument.

        """
        args = ("generate", "my.client.id", "-v")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_generate_invalid_refresh(self):
        """Test CLI.parse_command_args().

        'generate' subcommand with a bad '--refresh' option value.

        """
        args = ("generate", "my.client.id", "--refresh", "sometime")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_generate_missing_client_id_pattern(self):
        """Test CLI.parse_command_args().

        'generate' subcommand with no client id pattern argument.

        """
        args = ("generate")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_generate_with_refresh_seconds(self):
        """Test CLI.parse_command_args().

        Happy path. 'generate' subcommand with a '--refresh' argument.

        """
        cut = CLI()
        args = ("gen", "sam@i.am", "--refresh", "10")
        cut.parse_command_args(args)
        self.assertEqual('generate', cut.args.subcmd)
        self.assertEqual("sam@i.am", cut.args.clientIdPattern)
        self.assertEqual(10, cut.args.refresh)
        self.assertNotIn('counter', cut.args)
        self.assertNotIn('passwordLength', cut.args)
        self.assertNotIn('period', cut.args)
        self.assertNotIn('clientIdToAdd', cut.args)

    def test_parse_generate_with_refresh_once(self):
        """Test CLI.parse_command_args().

        Happy path. 'generate' subcommand with a '--refresh' argument.

        """
        cut = CLI()
        args = ("gen", "sam@i.am", "--refresh", "once")
        cut.parse_command_args(args)
        self.assertEqual('generate', cut.args.subcmd)
        self.assertEqual("sam@i.am", cut.args.clientIdPattern)
        self.assertEqual("once", cut.args.refresh)
        self.assertNotIn('counter', cut.args)
        self.assertNotIn('passwordLength', cut.args)
        self.assertNotIn('period', cut.args)
        self.assertNotIn('clientIdToAdd', cut.args)

    def test_parse_generate_with_refresh_expiration(self):
        """Test CLI.parse_command_args().

        Happy path. 'generate' subcommand with a '--refresh' argument.

        """
        cut = CLI()
        args = ("gen", "sam@i.am", "--refresh", "expiration")
        cut.parse_command_args(args)
        self.assertEqual('generate', cut.args.subcmd)
        self.assertEqual("sam@i.am", cut.args.clientIdPattern)
        self.assertEqual("expiration", cut.args.refresh)
        self.assertNotIn('counter', cut.args)
        self.assertNotIn('passwordLength', cut.args)
        self.assertNotIn('period', cut.args)
        self.assertNotIn('clientIdToAdd', cut.args)

    def test_parse_info(self):
        """Test CLI.parse_command_args().

        Happy path 'info' subcommand with no arguments.

        """
        cut = CLI()
        args = ("info",)
        cut.parse_command_args(args)
        self.assertFalse(cut.args.showVersion)
        self.assertEqual('info', cut.args.subcmd)
        self.assertNotIn('verbose', cut.args)
        self.assertNotIn('clientIdPattern', cut.args)
        self.assertNotIn('clientIdToAdd', cut.args)
        self.assertNotIn('passwordLength', cut.args)
        self.assertNotIn('period', cut.args)
        self.assertNotIn('counter', cut.args)

    def test_parse_info_invalid_args(self):
        """Test CLI.parse_command_args().

        'info' subcommand with extraneous arguments.

        """
        args = ("info", "-v")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_invalid_args(self):
        """Test CLI.parse_command_args().

        No subcommand, no valid arguments.

        """
        args = ("--xxx", "what", "-yz")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_invalid_subcommand(self):
        """Test CLI.parse_command_args().

        Bad subcommand.

        """
        args = ("nothing")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_list_all(self):
        """Test CLI.parse_command_args().

        Happy path 'list' subcommand with no arguments.

        """
        cut = CLI()
        args = ("list",)
        cut.parse_command_args(args)
        self.assertEqual('list', cut.args.subcmd)
        self.assertEqual("", cut.args.clientIdPattern)
        self.assertFalse(cut.args.verbose)
        self.assertNotIn('clientIdToAdd', cut.args)
        self.assertNotIn('passwordLength', cut.args)
        self.assertNotIn('period', cut.args)
        self.assertNotIn('counter', cut.args)

    def test_parse_list_all_verbose(self):
        """Test CLI.parse_command_args().

        Happy path 'list' subcommand the '-v' argument.

        """
        cut = CLI()
        args = ("list", "-v")
        cut.parse_command_args(args)
        self.assertEqual('list', cut.args.subcmd)
        self.assertEqual("", cut.args.clientIdPattern)
        self.assertTrue(cut.args.verbose)
        self.assertNotIn('clientIdToAdd', cut.args)
        self.assertNotIn('passwordLength', cut.args)
        self.assertNotIn('period', cut.args)
        self.assertNotIn('counter', cut.args)

    def test_parse_list_client_id_pattern(self):
        """Test CLI.parse_command_args().

        Happy path 'list' subcommand with a client id pattern and no arguments.

        """
        cut = CLI()
        args = ("list", "*wat*")
        cut.parse_command_args(args)
        self.assertEqual('list', cut.args.subcmd)
        self.assertEqual("*wat*", cut.args.clientIdPattern)
        self.assertFalse(cut.args.verbose)
        self.assertNotIn('clientIdToAdd', cut.args)
        self.assertNotIn('passwordLength', cut.args)
        self.assertNotIn('period', cut.args)
        self.assertNotIn('counter', cut.args)

    def test_parse_list_client_id_pattern_invalid_args(self):
        """Test CLI.parse_command_args().

        'list' subcommand with a client id pattern and a bad option argument.

        """
        args = ("list", "*wat*", "--pdq", "xyz")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_list_client_id_pattern_verbose(self):
        """Test CLI.parse_command_args().

        Happy path 'list' subcommand with a client id pattern and
        the '-v' argument.

        """
        cut = CLI()
        args = ("list", "*wat*", "-v")
        cut.parse_command_args(args)
        self.assertEqual('list', cut.args.subcmd)
        self.assertEqual("*wat*", cut.args.clientIdPattern)
        self.assertTrue(cut.args.verbose)
        self.assertNotIn('clientIdToAdd', cut.args)
        self.assertNotIn('passwordLength', cut.args)
        self.assertNotIn('period', cut.args)
        self.assertNotIn('counter', cut.args)

    def test_parse_list_invalid_args(self):
        """Test CLI.parse_command_args().

        'list' subcommand with a bad option argument.

        """
        args = ("list", "--pdq", "xyz")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_set_client_id(self):
        """Test CLI.parse_command_args().

        Happy path set clientid.

        """
        cut = CLI()
        args = (
            "set", "clientid",
            "Wat:captian@beefheart.org", "Wat:captain@beefheart.org")
        cut.parse_command_args(args)
        self.assertIn('subcmd', cut.args)
        self.assertEqual('set', cut.args.subcmd)
        self.assertIn('subsubcmd', cut.args)
        self.assertEqual('clientid', cut.args.subsubcmd)
        self.assertIn('oldClientId', cut.args)
        self.assertEqual("Wat:captian@beefheart.org", cut.args.oldClientId)
        self.assertIn('newClientId', cut.args)
        self.assertEqual("Wat:captain@beefheart.org", cut.args.newClientId)

    def test_parse_set_client_id_missing_args(self):
        """Test CLI.parse_command_args().

        'set clientid' subcommand with a missing newClientId argument.

        """
        args = (
            "set", "clientid",
            "Wat:captian@beefheart.org")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_set_client_id_wildcard_old_id(self):
        """Test CLI.parse_command_args().

        Trying to set clientid, but specified a wildcard in the old id string.

        """
        expected_err_msg = (
            "authenticator: error: oldClientId must be an exact match; " +
            "no wildcards\n", )
        rw_mock = unittest.mock.MagicMock()
        cut = CLI(stdout=rw_mock, stderr=rw_mock)
        args = (
            "set", "clientid",
            "Wat:*@beefheart.org", "Wat:captain@beefheart.org")
        with self.assertRaises(SystemExit):
            cut.parse_command_args(args)
        self.assertEqual(2, rw_mock.write.call_count)
        self.assertEqual(expected_err_msg, rw_mock.write.call_args_list[1][0])

    def test_parse_set_client_id_wildcard_new_id(self):
        """Test CLI.parse_command_args().

        Trying to set clientid, but specified a wildcard in the new id string.

        """
        expected_err_msg = (
            "authenticator: error: newClientId must not be a " +
            "wildcard string\n", )
        rw_mock = unittest.mock.MagicMock()
        cut = CLI(stdout=rw_mock, stderr=rw_mock)
        args = (
            "set", "clientid",
            "Wat:captian@beefheart.org", "Wat:*@beefheart.org")
        with self.assertRaises(SystemExit):
            cut.parse_command_args(args)
        self.assertEqual(2, rw_mock.write.call_count)
        self.assertEqual(expected_err_msg, rw_mock.write.call_args_list[1][0])

    def test_parse_set_passphrase(self):
        """Test CLI.parse_command_args().

        Happy path set passphrase.

        """
        cut = CLI()
        args = ("set", "passphrase")
        cut.parse_command_args(args)
        self.assertIn('subcmd', cut.args)
        self.assertEqual('set', cut.args.subcmd)
        self.assertIn('subsubcmd', cut.args)
        self.assertEqual('passphrase', cut.args.subsubcmd)

    def test_parse_set_passphrase_extra_args(self):
        """Test CLI.parse_command_args().

        'set passphrase' subcommand with an extraneous oldClientId argument.

        """
        args = (
            "set", "passphrase",
            "Wat:captian@beefheart.org")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    def test_parse_version(self):
        """Test CLI.parse_command_args().

        Happy path '--version' argument.

        """
        cut = CLI()
        args = ("--version",)
        cut.parse_command_args(args)
        self.assertTrue(cut.args.showVersion)
        self.assertNotIn('subcmd', cut.args)

    def test_parse_version_override(self):
        """Test CLI.parse_command_args().

        '--version' argument, with extra stuff. Expect --version to have
        precidence.

        """
        cut = CLI()
        args = ("--version", "info")
        cut.parse_command_args(args)
        self.assertTrue(cut.args.showVersion)
        self.assertIsNone(cut.args.subcmd)

    def test_parse_version_invalid_args(self):
        """Test CLI.parse_command_args().

        '--version' argument, with extra invalid stuff.

        """
        args = ("--version", "wat")
        with self.assertRaises(SystemExit):
            with CoreCLITests.RedirectStdStreams(
                    stdout=self.devnull, stderr=self.devnull):
                cut = CLI()
                cut.parse_command_args(args)

    # ------------------------------------------------------------------------+
    # tests for CLI.create_data_file()
    # ------------------------------------------------------------------------+

    @unittest.mock.patch('os.path.expanduser')
    def test_add_with_new_file_created(self, mock_expanduser):
        """Test CLI.create_data_file().

        Happy path test adding a time-based HOTP with no initial data file.

        """
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_passphrase = "Maresy doats and dosey doats."
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "sam@i.am")
        cut.parse_command_args(args)
        cut.create_data_file()
        calls = [
            unittest.mock.call.write(
                "No data file was found. Do you want to create your data" +
                " file? (yes|no) [yes]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Confirm passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline()]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(6, rw_mock.write.call_count)
        self.assertEqual(3, rw_mock.flush.call_count)
        self.assertEqual(3, rw_mock.readline.call_count)
        self.assertEqual(expected_passphrase, cut._CLI__passphrase)

    @unittest.mock.patch('os.path.expanduser')
    def test_add_with_new_file_created_by_default(self, mock_expanduser):
        """Test CLI.create_data_file().

        Happy path test adding a time-based HOTP with no initial data file,
        taking the default from the prompt about whether to create a new
        data file.

        """
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_passphrase = "Maresy doats and dosey doats."
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            '', expected_passphrase, expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "sam@i.am")
        cut.parse_command_args(args)
        cut.create_data_file()
        calls = [
            unittest.mock.call.write(
                "No data file was found. Do you want to create your data" +
                " file? (yes|no) [yes]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Confirm passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline()]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(6, rw_mock.write.call_count)
        self.assertEqual(3, rw_mock.flush.call_count)
        self.assertEqual(3, rw_mock.readline.call_count)
        self.assertEqual(expected_passphrase, cut._CLI__passphrase)
        self.assertEqual(expected_passphrase, cut._CLI__passphrase)

    @unittest.mock.patch('os.path.expanduser')
    def test_add_with_new_file_refused(self, mock_expanduser):
        """Test CLI.create_data_file().

        Happy path test adding a time-based HOTP but refusing to create
        a new data file.

        """
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'no']
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "sam@i.am")
        cut.parse_command_args(args)
        cut.create_data_file()
        calls = [
            unittest.mock.call.write(
                "No data file was found. Do you want to create your data" +
                " file? (yes|no) [yes]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline()]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(2, rw_mock.write.call_count)
        self.assertEqual(1, rw_mock.flush.call_count)
        self.assertEqual(1, rw_mock.readline.call_count)

    # ------------------------------------------------------------------------+
    # tests for CLI.prompt_for_secrets()
    # ------------------------------------------------------------------------+

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_add_counter_based_hotp(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.prompt_for_secrets().

        Happy path test adding a counter-based HOTP.

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_passphrase = "Maresy doats and dosey doats."
        expected_shared_secret = "ABCDEFGHABCDEFGHABCDEFGH"
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, expected_passphrase,
            expected_shared_secret]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "sam@i.am", "--counter", "9")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write(
                "No data file was found. Do you want to create your data" +
                " file? (yes|no) [yes]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Confirm passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter shared secret: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline()]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(8, rw_mock.write.call_count)
        self.assertEqual(4, rw_mock.flush.call_count)
        self.assertEqual(4, rw_mock.readline.call_count)
        self.assertEqual(expected_passphrase, cut._CLI__passphrase)
        self.assertEqual(expected_passphrase, cut._CLI__passphrase)
        self.assertEqual(expected_shared_secret, cut._CLI__shared_secret)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_add_counter_based_hotp_new_data_refused(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.prompt_for_secrets().

        Happy path test adding a counter-based HOTP, but refusing to create
        a new data file.

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'no']
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "sam@i.am", "--counter", "9")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write(
                "No data file was found. Do you want to create your data" +
                " file? (yes|no) [yes]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline()]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(2, rw_mock.write.call_count)
        self.assertEqual(1, rw_mock.flush.call_count)
        self.assertEqual(1, rw_mock.readline.call_count)
        self.assertIsNone(cut._CLI__passphrase)
        self.assertIsNone(cut._CLI__shared_secret)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_add_time_based_hotp(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.Prompt().

        Happy path test adding a time-based HOTP.

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_passphrase = "Maresy doats and dosey doats."
        expected_shared_secret = "ABCDEFGHABCDEFGHABCDEFGH"
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, expected_passphrase,
            expected_shared_secret]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "sam@i.am")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write(
                "No data file was found. Do you want to create your data" +
                " file? (yes|no) [yes]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Confirm passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter shared secret: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline()]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(8, rw_mock.write.call_count)
        self.assertEqual(4, rw_mock.flush.call_count)
        self.assertEqual(4, rw_mock.readline.call_count)
        self.assertEqual(expected_passphrase, cut._CLI__passphrase)
        self.assertEqual(expected_shared_secret, cut._CLI__shared_secret)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_add_time_based_hotp_googlized_secret(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.Prompt().

        Happy path test adding a time-based HOTP, using a shared secret
        entered in the Google style (lower case, embedded spaces).

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_passphrase = "Maresy doats and dosey doats."
        expected_shared_secret = "ABCDEFGHABCDEFGHABCDEFGH"
        provided_shared_secret = "abcd efgh abcd efgh abcd efgh"
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, expected_passphrase,
            provided_shared_secret]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "sam@i.am")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write(
                "No data file was found. Do you want to create your data" +
                " file? (yes|no) [yes]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Confirm passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter shared secret: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline()]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(8, rw_mock.write.call_count)
        self.assertEqual(4, rw_mock.flush.call_count)
        self.assertEqual(4, rw_mock.readline.call_count)
        self.assertEqual(expected_passphrase, cut._CLI__passphrase)
        self.assertEqual(expected_shared_secret, cut._CLI__shared_secret)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_add_time_based_hotp_empty_secret(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.Prompt().

        Provide an empty secret to exit the interaction.

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_passphrase = "Maresy doats and dosey doats."
        provided_shared_secret = ""
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, expected_passphrase,
            provided_shared_secret]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "sam@i.am")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write(
                "No data file was found. Do you want to create your data" +
                " file? (yes|no) [yes]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Confirm passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter shared secret: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline()]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(8, rw_mock.write.call_count)
        self.assertEqual(4, rw_mock.flush.call_count)
        self.assertEqual(4, rw_mock.readline.call_count)
        self.assertEqual(expected_passphrase, cut._CLI__passphrase)
        self.assertIsNone(cut._CLI__shared_secret)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_add_time_based_hotp_empty_passphrase(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.Prompt().

        Provide an empty passphrase to exit the interaction.

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_passphrase = "Maresy doats and dosey doats."
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, ""]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "sam@i.am")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write(
                "No data file was found. Do you want to create your data" +
                " file? (yes|no) [yes]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Confirm passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline()]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(6, rw_mock.write.call_count)
        self.assertEqual(3, rw_mock.flush.call_count)
        self.assertEqual(3, rw_mock.readline.call_count)
        self.assertIsNone(cut._CLI__passphrase)
        self.assertIsNone(cut._CLI__shared_secret)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_add_time_based_hotp_unmatched_passphrase(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.Prompt().

        Initially provide an unmatched passphrase.

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_passphrase = "Maresy doats and dosey doats."
        confirmed_passphrase = "Mares eat oats and does eat oats."
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, confirmed_passphrase,
            expected_passphrase, expected_passphrase, ""]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("add", "sam@i.am")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write(
                "No data file was found. Do you want to create your data" +
                " file? (yes|no) [yes]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Confirm passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Passphrases do not match. Try again."),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("Enter passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Confirm passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter shared secret: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline()]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(14, rw_mock.write.call_count)
        self.assertEqual(6, rw_mock.flush.call_count)
        self.assertEqual(6, rw_mock.readline.call_count)
        self.assertEqual(expected_passphrase, cut._CLI__passphrase)
        self.assertIsNone(cut._CLI__shared_secret)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_delete_no_data(self, mock_expanduser, mock_key_stretches):
        """Test CLI.prompt_for_secrets().

        Happy path test deleting a HOTP configuration, but no data file.

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        rw_mock = unittest.mock.MagicMock()
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("delete", "sam@i.am")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write(
                "No data file was found; cannot complete request."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(2, rw_mock.write.call_count)
        self.assertIsNone(cut._CLI__passphrase)
        self.assertIsNone(cut._CLI__shared_secret)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_generate_no_data(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.prompt_for_secrets().

        Happy path test generate a HOTP password, but no data file.

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        rw_mock = unittest.mock.MagicMock()
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("generate", )
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write(
                "No data file was found; cannot complete request."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(2, rw_mock.write.call_count)
        self.assertIsNone(cut._CLI__passphrase)
        self.assertIsNone(cut._CLI__shared_secret)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_list_no_data(self, mock_expanduser, mock_key_stretches):
        """Test CLI.prompt_for_secrets().

        Happy path test list HOTP configurations, but no data file.

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        rw_mock = unittest.mock.MagicMock()
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("list", )
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write(
                "No data file was found; cannot complete request."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(2, rw_mock.write.call_count)
        self.assertIsNone(cut._CLI__passphrase)
        self.assertIsNone(cut._CLI__shared_secret)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_set_passphrase_no_data(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.prompt_for_secrets().

        Happy path test set data file passphrase, but no data file.

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        rw_mock = unittest.mock.MagicMock()
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("set", "passphrase")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write(
                "No data file was found; cannot complete request."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(2, rw_mock.write.call_count)
        self.assertIsNone(cut._CLI__passphrase)
        self.assertIsNone(cut._CLI__new_passphrase)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_set_passphrase(self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that setting the passphrase captures the new passphrase.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        expected_new_passphrase = "And little lambsy divey."
        self._add_three_hotp_to_file(expected_passphrase)
        # Change the passphrase
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase,
            expected_new_passphrase, expected_new_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("set", "passphrase")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write("Enter passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Enter new passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Confirm new passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline()]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(6, rw_mock.write.call_count)
        self.assertEqual(3, rw_mock.flush.call_count)
        self.assertEqual(3, rw_mock.readline.call_count)
        self.assertEqual(expected_passphrase, cut._CLI__passphrase)
        self.assertEqual(expected_new_passphrase, cut._CLI__new_passphrase)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_set_client_id_no_data(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.prompt_for_secrets().

        Happy path test set clientid, but no data file.

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        rw_mock = unittest.mock.MagicMock()
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = (
            "set", "clientid",
            "Wat:captian@beefheart.org", "Wat:captain@beefheart.org")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write(
                "No data file was found; cannot complete request."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(2, rw_mock.write.call_count)
        self.assertIsNone(cut._CLI__passphrase)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_prompt_set_client_id(self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that setting a clientid prompts for the passphrase.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Change the clientId
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = (
            "set", "clientid",
            "012345@nom.deplume", "123456@wat.deplume")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        calls = [
            unittest.mock.call.write("Enter passphrase: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline()]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(2, rw_mock.write.call_count)
        self.assertEqual(1, rw_mock.flush.call_count)
        self.assertEqual(1, rw_mock.readline.call_count)
        self.assertEqual(expected_passphrase, cut._CLI__passphrase)
        self.assertIsNone(cut._CLI__new_passphrase)

    # ------------------------------------------------------------------------+
    # test for CLI.execute()
    # ------------------------------------------------------------------------+

    # 'add' tests
    #

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_add_one_time_based_hotp(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that a HOTP configuration can be added.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_data_file = os.path.join(
            expected_data_dir, "authenticator.data")
        expected_passphrase = "Maresy doats and dosey doats."
        expected_shared_secret = "GEZDGNBVGY2TQOJQGEZDGNBVGY2TQOJQ"
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, expected_passphrase,
            expected_shared_secret]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("add", "012345@nom.deplume")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        self.assertTrue(os.path.exists(expected_data_file))
        calls = [
            unittest.mock.call.write("OK"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_add_one_time_based_hotp_twice(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that adding a HOTP configuration that already exists will
        fail with an appropriate error message.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_data_file = os.path.join(
            expected_data_dir, "authenticator.data")
        expected_passphrase = "Maresy doats and dosey doats."
        expected_shared_secret = "ABCDEFGHABCDEFGHABCDEFGH"
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, expected_passphrase,
            expected_shared_secret]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("add", "012345@nom.deplume")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write("OK"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # Second attempt (which should fail)
        #
        rw_mock.reset_mock()
        rw_mock.readline.side_effect = [
            expected_passphrase, expected_shared_secret]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        self.assertEqual(expected_data_file, cut._CLI__data_file)
        args = ("add", "012345@nom.deplume")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write(
                "Add failed. That configuration already exists."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_add_one_time_based_hotp_googlized_secret(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that a HOTP configuration can be added using a secret
        that is lowercase with embedded spaces.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_data_file = os.path.join(
            expected_data_dir, "authenticator.data")
        expected_passphrase = "Maresy doats and dosey doats."
        googlized_shared_secret = "gezd gnbv gy2t qojq gezd gnbv gy2t qojq"
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, expected_passphrase,
            googlized_shared_secret]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("add", "012345@nom.deplume")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        self.assertTrue(os.path.exists(expected_data_file))
        calls = [
            unittest.mock.call.write("OK"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_add_to_alt_file_one_time_based_hotp(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that a HOTP configuration can be added.

        """
        import os.path
        import os

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        initial_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_data_dir = os.path.join(
            self.temp_dir_path2.name, ".authenticator")
        os.makedirs(expected_data_dir, mode=0o766)
        expected_data_file = os.path.join(
            expected_data_dir, "authenticator.data")
        expected_passphrase = "Maresy doats and dosey doats."
        expected_shared_secret = "GEZDGNBVGY2TQOJQGEZDGNBVGY2TQOJQ"
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            'yes', expected_passphrase, expected_passphrase,
            expected_shared_secret]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(initial_data_dir, cut._CLI__data_dir)
        args = ("--data", expected_data_file, "add", "012345@nom.deplume")
        cut.parse_command_args(args)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        self.assertTrue(os.path.exists(expected_data_file))
        calls = [
            unittest.mock.call.write("OK"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)

    # 'delete' tests
    #

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_delete_all_config(self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting the last config works properly.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Delete the configuration
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("delete", "*", "-q")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write("Deleted 3 configurations."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # List the configuration
        #
        self._assert_configuration_count_from_file(expected_passphrase, 0)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_delete_all_config_confirmed(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting all configurations works properly, with a
        confirmation prompt for each.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Delete the configuration
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("delete", "*")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        rw_mock.readline.side_effect = [
            "yes", "yes", "yes"]
        cut.execute()
        calls = [
            unittest.mock.call.write(
                "Delete 012345@nom.deplume? (yes|no) [no]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write(
                "Delete mickey@prisney.com? (yes|no) [no]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write(
                "Delete donald@prisney.com? (yes|no) [no]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Deleted 3 configurations."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # List the configuration
        #
        self._assert_configuration_count_from_file(expected_passphrase, 0)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_delete_all_config_declined(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting all configurations, with a confirmation prompt
        for each, does not delete anything if the default response is
        supplied each time.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Delete the configuration
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("delete", "*")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        rw_mock.readline.side_effect = [
            "", "", ""]
        cut.execute()
        calls = [
            unittest.mock.call.write(
                "Delete 012345@nom.deplume? (yes|no) [no]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write(
                "Delete mickey@prisney.com? (yes|no) [no]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write(
                "Delete donald@prisney.com? (yes|no) [no]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("No configurations deleted."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # List the configuration
        #
        self._assert_configuration_count_from_file(expected_passphrase, 3)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_delete_one_config_declined_explicitly(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting does not take place with the confirmation prompt
        has a "no" response.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Delete the configuration
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("delete", "012345@nom.deplume")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        rw_mock.readline.side_effect = [
            "no"]
        cut.execute()
        calls = [
            unittest.mock.call.write(
                "Delete 012345@nom.deplume? (yes|no) [no]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("No configurations deleted."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # List the configuration
        #
        self._assert_configuration_count_from_file(expected_passphrase, 3)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_delete_one_config(self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting one of the several configurations works properly.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Delete the configuration
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("delete", "012345@nom.deplume", "-q")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write("Deleted 1 configuration."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # List the configuration
        #
        self._assert_configuration_count_from_file(expected_passphrase, 2)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_delete_one_config_confirmed(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting, with confirmation prompt, one of the several
        configurations works properly.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Delete the configuration
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("delete", "012345@nom.deplume")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        rw_mock.readline.side_effect = [
            "yes"]
        cut.execute()
        calls = [
            unittest.mock.call.write(
                    "Delete 012345@nom.deplume? (yes|no) [no]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Deleted 1 configuration."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # List the configuration
        #
        self._assert_configuration_count_from_file(expected_passphrase, 2)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_delete_one_config_declined_by_default(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting does not take place with the confirmation prompt
        has the default response (no).

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Delete the configuration
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("delete", "012345@nom.deplume")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        rw_mock.readline.side_effect = [
            ""]
        cut.execute()
        calls = [
            unittest.mock.call.write(
                "Delete 012345@nom.deplume? (yes|no) [no]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("No configurations deleted."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # List the configuration
        #
        self._assert_configuration_count_from_file(expected_passphrase, 3)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_delete_the_only_config(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting the last config works properly.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configuration
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_one_time_based_hotp_to_file(expected_passphrase)
        # Delete the configuration
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("delete", "012345@nom.deplume", "--quiet")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write("Deleted 1 configuration."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # List the configuration
        #
        self._assert_configuration_count_from_file(expected_passphrase, 0)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_delete_the_only_config_confirmed(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting, with a confirmation prompt, one of the several
        configurations works properly.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configuration
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_one_time_based_hotp_to_file(expected_passphrase)
        # Delete the configuration
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("delete", "012345@nom.deplume")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        rw_mock.readline.side_effect = [
            "yes"]
        cut.execute()
        calls = [
            unittest.mock.call.write(
                "Delete 012345@nom.deplume? (yes|no) [no]: "),
            unittest.mock.call.write(""),
            unittest.mock.call.flush(),
            unittest.mock.call.readline(),
            unittest.mock.call.write("Deleted 1 configuration."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # List the configuration
        #
        self._assert_configuration_count_from_file(expected_passphrase, 0)

    # 'generate' tests
    #

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_generate_time_based_hotp_one_config_once(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting one of the several configurations works properly.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Generate the codes
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("generate", "012345@nom.deplume", "--refresh", "once")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        self.assertEqual(2, rw_mock.write.call_count)
        call_args, call_kwargs = rw_mock.write.call_args_list[0]
        is_response_ok = re.compile(
            "^012345@nom.deplume: [0-9]{6} \(expires in [0-9]{1,2} seconds\)$")
        self.assertIsNotNone(is_response_ok.match(call_args[0]))

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_generate_time_based_hotp_all_config_once(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting one of the several configurations works properly.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Generate the codes
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("generate", "*", "--refresh", "once")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        self.assertEqual(4, rw_mock.write.call_count)
        call_args, call_kwargs = rw_mock.write.call_args_list[0]
        is_response_ok = re.compile(
            "^012345@nom.deplume: [0-9]{6} \(expires in [0-9]{1,2} seconds\)$")
        self.assertIsNotNone(is_response_ok.match(call_args[0]))
        call_args, call_kwargs = rw_mock.write.call_args_list[2]
        is_response_ok = re.compile(
            "^donald@prisney.com: [0-9]{6} \(expires in [0-9]{1,2} seconds\)$")
        self.assertIsNotNone(is_response_ok.match(call_args[0]))

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_generate_counter_based_hotp_one_config_once(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting one of the several configurations works properly.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Generate the codes
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("generate", "mickey@prisney.com", "-c")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        self.assertEqual(2, rw_mock.write.call_count)
        call_args, call_kwargs = rw_mock.write.call_args_list[0]
        is_response_ok = re.compile(
            "^mickey@prisney.com: [0-9]{6} \(for count 12\)$")
        self.assertIsNotNone(is_response_ok.match(call_args[0]))

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_generate_counter_based_hotp_one_config_twice(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting one of the several configurations works properly.

        """
        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Generate the codes
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("generate", "mickey@prisney.com", "-c")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        self.assertEqual(2, rw_mock.write.call_count)
        call_args, call_kwargs = rw_mock.write.call_args_list[0]
        is_response_ok = re.compile(
            "^mickey@prisney.com: [0-9]{6} \(for count 12\)$")
        self.assertIsNotNone(is_response_ok.match(call_args[0]))
        # Again
        #
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        args = ("generate", "mickey@prisney.com", "--counter-based")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        self.assertEqual(2, rw_mock.write.call_count)
        call_args, call_kwargs = rw_mock.write.call_args_list[0]
        is_response_ok = re.compile(
            "^mickey@prisney.com: [0-9]{6} \(for count 13\)$")
        self.assertIsNotNone(is_response_ok.match(call_args[0]))

    # 'list' tests
    #

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_list_with_no_data(self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that the correct response is provided when no data is found.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        rw_mock = unittest.mock.MagicMock()
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("list", )
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        cut.execute()
        calls = [
            unittest.mock.call.write(
                "No data file was found; cannot complete request."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_list_with_one_config(self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that the correct response is provided when just one configuration
        is found.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configuration
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_one_time_based_hotp_to_file(expected_passphrase)
        # List the configuration
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("list", )
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write(""),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("012345@nom.deplume"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(4, rw_mock.write.call_count)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_list_with_one_config_verbose(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that the correct verbose response is provided when just one
        configuration is found.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configuration
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_one_time_based_hotp_to_file(expected_passphrase)
        # List the configuration
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("list", "-v")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write(""),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("id: 012345@nom.deplume"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("time-based; period: 30"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("password length: 6"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(8, rw_mock.write.call_count)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_list_with_three_configs(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that the correct response is provided when several configurations
        are found.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # List the configurations
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("list", )
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write(""),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("012345@nom.deplume"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("mickey@prisney.com"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("donald@prisney.com"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(8, rw_mock.write.call_count)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_list_with_three_configs_verbose(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that the correct verbose response is provided when just one
        configuration is found.

        """
        import os.path
        from datetime import datetime

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        now = datetime.now(self.__tz)
        # List the configurations
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("list", "-v")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write(""),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("id: 012345@nom.deplume"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("time-based; period: 30"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("password length: 6"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write(""),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("id: mickey@prisney.com"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("counter-based; last counter: 11"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write(
                "count updated: {0}".format(
                    now.strftime("%Y-%m-%d %H:%M:%S %z"))),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("password length: 6"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write(""),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("id: donald@prisney.com"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("time-based; period: 20"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("password length: 6"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(26, rw_mock.write.call_count)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_list_with_wildcard_default(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that the correct response is provided when several configurations
        are found with a wildcard pattern having no '*' chars.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # List the configurations
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("list", "pris")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write(""),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("mickey@prisney.com"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("donald@prisney.com"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(6, rw_mock.write.call_count)

    # set passphrase tests
    #

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_execute_set_passphrase(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Check that deleting the last config works properly.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        expected_new_passphrase = "And little lambsy divey."
        self._add_three_hotp_to_file(expected_passphrase)
        # Change the passphrase
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase,
            expected_new_passphrase, expected_new_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("set", "passphrase")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write("OK"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # List the configurations
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_new_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("list", )
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write(""),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("012345@nom.deplume"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("mickey@prisney.com"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("donald@prisney.com"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(8, rw_mock.write.call_count)

    # set clientid tests
    #

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_execute_set_client_id(self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Happy path for changing a client id; check that the change takes place.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Change the clientId
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock, stderr=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = (
            "set", "clientid",
            "012345@nom.deplume", "123456@wat.deplume")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write("OK"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        # List the configurations
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("list", )
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write(""),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("123456@wat.deplume"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("mickey@prisney.com"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("donald@prisney.com"),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(8, rw_mock.write.call_count)

    @unittest.mock.patch('authenticator.data.ClientFile._get_key_stretches')
    @unittest.mock.patch('os.path.expanduser')
    def test_execute_set_client_id_missing_client(
            self, mock_expanduser, mock_key_stretches):
        """Test CLI.execute().

        Try changing a clientid for a HOTP configuration that does not exist.

        """
        import os.path

        mock_key_stretches.return_value = 64
        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        # Add the configurations
        #
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_passphrase = "Maresy doats and dosey doats."
        self._add_three_hotp_to_file(expected_passphrase)
        # Change the clientId
        #
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock, stderr=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = (
            "set", "clientid",
            "wack.a.mole", "i.m@arod.end")
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write(
                "No configuration found with client ID 'wack.a.mole'"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write("Nothing changed."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)

    # miscellaneous tests
    #

    @unittest.mock.patch('os.path.expanduser')
    def test_locate_default_data_dir(self, mock_expanduser):
        """Test CLI.execute().

        Check that the default directory is chosen properly.

        """
        import os.path

        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        cut = CLI()
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)

    @unittest.mock.patch('os.path.expanduser')
    def test_locate_default_data_file(self, mock_expanduser):
        """Test CLI.execute().

        Check that the default filepath is generated properly.

        """
        import os.path

        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_data_file = os.path.join(
            expected_data_dir, "authenticator.data")
        expected_passphrase = "Maresy doats and dosey doats."
        rw_mock = unittest.mock.MagicMock()
        rw_mock.readline.side_effect = [
            expected_passphrase]
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_file, cut._CLI__data_file)

    @unittest.mock.patch('os.path.expanduser')
    def test_show_version(self, mock_expanduser):
        """Test CLI.execute().

        Make certain the --version option produces correct output.

        """
        import os.path
        import authenticator

        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        rw_mock = unittest.mock.MagicMock()
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("--version", )
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write(
                "authenticator version {0}".format(authenticator.__version__)),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(2, rw_mock.write.call_count)

    @unittest.mock.patch('os.path.expanduser')
    def test_show_info(self, mock_expanduser):
        """Test CLI.execute().

        Make certain the info subcommand produces correct output.

        """
        import os.path
        import authenticator

        mock_expanduser.side_effect = \
            lambda x: self._side_effect_expand_user(x)
        expected_data_dir = os.path.join(
            self.temp_dir_path.name, ".authenticator")
        expected_data_file = os.path.join(
            expected_data_dir, "authenticator.data")
        rw_mock = unittest.mock.MagicMock()
        cut = CLI(stdin=rw_mock, stdout=rw_mock)
        self.assertEqual(expected_data_dir, cut._CLI__data_dir)
        args = ("info", )
        cut.parse_command_args(args)
        cut.create_data_file()
        cut.prompt_for_secrets()
        rw_mock.reset_mock()
        cut.execute()
        calls = [
            unittest.mock.call.write(
                "authenticator version {0}".format(authenticator.__version__)),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write(
                "Copyright (c) 2016 David T. Hein."),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write(
                "MIT License. See https://opensource.org/licenses/MIT"),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write(
                "\nData file location: {0}".format(
                    expected_data_file)),
            unittest.mock.call.write("\n"),
            unittest.mock.call.write(
                "\nSee https://github.com/jenesuispasdave/github/ for the " +
                "source code repository,\nthe latest version, and " +
                "technical support."),
            unittest.mock.call.write("\n")]
        rw_mock.assert_has_calls(calls)
        self.assertEqual(10, rw_mock.write.call_count)
