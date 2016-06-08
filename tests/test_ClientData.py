# This Source Code Form is subject to the terms of the MIT License.
# If a copy of the MIT License was not distributed with this
# file, you can obtain one at https://opensource.org/licenses/MIT.
#
"""Unit tests for ClientData.py."""
import unittest
import iso8601
from datetime import datetime
from authenticator import ClientData, ClientDataEncoder, ClientDataDecoder


class CoreClientDataTests(unittest.TestCase):
    """Tests for the data module."""

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
        dt = ut - lt
        offset_minutes = 0
        if (0 == dt.days):
            offset_minutes = dt.seconds // 60
        else:
            dt = lt - ut
            offset_minutes = dt.seconds // 60
            offset_minutes *= -1
        dt = timedelta(minutes=offset_minutes)
        self.__tz = timezone(dt)
        self.__utz = timezone(timedelta(0))

        super().__init__(*args)

    def setUp(self):
        """Create data used by the test cases."""
        self.isoFmt = "%Y%m%dT%H%M%S%z"
        self.jsonStringExample01 = "\n".join((
            "{",
            '    "clientId": "What.Ever.Dude",',
            '    "counterFromTime": true,',
            '    "lastCount": 0,',
            '    "lastCountUpdateTime": "00010101T000000+0000",',
            '    "note": "",',
            '    "passwordLength": 6,',
            '    "period": 30,',
            '    "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",',
            '    "tags": []',
            "}"))
        self.jsonStringExample02 = "\n".join((
            "{",
            '    "clientId": "You.Dont.Say",',
            '    "counterFromTime": false,',
            '    "lastCount": 99,',
            '    "lastCountUpdateTime": "20130704T131415-0500",',
            '    "note": "This is not a note.",',
            '    "passwordLength": 6,',
            '    "period": 30,',
            '    "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",',
            '    "tags": [',
            '        "test",',
            '        "none"',
            '    ]',
            "}"))
        self.jsonStringExample03 = "\n".join((
            "{",
            '    "clientId": "Well.I.Never",',
            '    "counterFromTime": true,',
            '    "lastCount": 0,',
            '    "lastCountUpdateTime": "00010101T000000+0000",',
            '    "note": "Man who sit on tack better off.",',
            '    "passwordLength": 8,',
            '    "period": 15,',
            '    "sharedSecret": "ABCDGNBVGY3TQOJQGEZDGNBVGY3TQCBA",',
            '    "tags": [',
            '        "AWS"',
            '    ]',
            "}"))

    def test_noop(self):
        """Excercise tearDown and setUp methods.

        This test does nothing itself. It is useful to test the tearDown()
        and setUp() methods in isolation (without side effects).

        """
        return

    # -------------------------------------------------------------------------
    # Tests for ClientData.__init__()
    # -------------------------------------------------------------------------

    def test_constructor_bad_client_id_type(self):
        """Test for __init__().

        Pass bad value type as client_id.

        """
        args = {
            "clientId": b'What.Ever.Dude',
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        with self.assertRaises(TypeError):
            ClientData(**args)

    def test_constructor_no_client_id(self):
        """Test for __init__().

        No client_id provided.

        """
        args = {
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        with self.assertRaises(ValueError):
            ClientData(**args)

    def test_constructor_empty_client_id(self):
        """Test for __init__().

        Empty client_id provided.

        """
        args = {
            "clientId": "",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        with self.assertRaises(ValueError):
            ClientData(**args)

    def test_constructor_bad_shared_secret_type(self):
        """Test for __init__().

        Pass bad value type as shared_secret.

        """
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": 1234567890
        }
        with self.assertRaises(TypeError):
            ClientData(**args)

    def test_constructor_no_shared_secret(self):
        """Test for __init__().

        No shared_secret provided.

        """
        args = {
            "clientId": "What.Ever.Dude"
        }
        with self.assertRaises(ValueError):
            ClientData(**args)

    def test_constructor_empty_shared_secret(self):
        """Test for __init__().

        Empty shared_secret provided.

        """
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": ""
        }
        with self.assertRaises(ValueError):
            ClientData(**args)

    def test_constructor_counter_from_time(self):
        """Test for __init__().

        Happy path counter_from_time.

        """
        # default
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        cut = ClientData(**args)
        self.assertTrue(cut.counter_from_time())
        # set true
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "counterFromTime": True
        }
        cut = ClientData(**args)
        self.assertTrue(cut.counter_from_time())
        # set false
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "counterFromTime": False
        }
        cut = ClientData(**args)
        self.assertFalse(cut.counter_from_time())
        # set zero
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "counterFromTime": 0
        }
        cut = ClientData(**args)
        self.assertFalse(cut.counter_from_time())
        # set None
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "counterFromTime": None
        }
        cut = ClientData(**args)
        self.assertFalse(cut.counter_from_time())
        # set 1
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "counterFromTime": 1
        }
        cut = ClientData(**args)
        self.assertTrue(cut.counter_from_time())
        # set "0"
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "counterFromTime": "0"
        }
        cut = ClientData(**args)
        self.assertTrue(cut.counter_from_time())

    def test_constructor_last_count(self):
        """Test for __init__().

        Happy path last_count.

        """
        # default
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        cut = ClientData(**args)
        self.assertEqual(0, cut.last_count())
        # 112
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "lastCount": 112
        }
        cut = ClientData(**args)
        self.assertEqual(112, cut.last_count())
        # "112"
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "lastCount": "112"
        }
        cut = ClientData(**args)
        self.assertEqual(112, cut.last_count())

    def test_constructor_last_count_bad_type(self):
        """Test for __init__().

        Pass last_count with an invalid type (not convertable to int).

        """
        # (112, 113, 114)
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "lastCount": (112, 113, 114)
        }
        with self.assertRaises(TypeError):
            ClientData(**args)

    def test_constructor_last_count_bad_value(self):
        """Test for __init__().

        Pass last_count with a negative value.

        """
        # (112, 113, 114)
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "lastCount": -112
        }
        with self.assertRaises(ValueError):
            ClientData(**args)

    def test_constructor_last_count_update_time(self):
        """Test for __init__().

        Happy path last_count_update_time.

        """
        # default
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        cut = ClientData(**args)
        expected = datetime(
            1, 1, 1, 0, 0, 0, 0, self.__utz).strftime(self.isoFmt)
        self.assertEqual(expected, cut.last_count_update_time())
        # unix epoch time
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "lastCountUpdateTime": "19700101T000000-0000"
        }
        cut = ClientData(**args)
        expected = iso8601.parse_date("19700101T000000-0000")
        expected = expected.strftime(self.isoFmt)
        self.assertEqual(expected, cut.last_count_update_time())
        # # arbitrary US central daylight time
        # #
        # # First check whether dateutil.parser recognizes the timezone
        # # 'CDT'. If it does, proceed with this check.
        # #
        # dt = parser.parse("Jul 25, 2013 20:21 CDT")
        # if dt.strftime(self.isoFmt).endswith("-0500"):
        #     args = {
        #         "clientId": "What.Ever.Dude",
        #         "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
        #         "lastCountUpdateTime": "Jul 25, 2013 20:21 CDT"
        #     }
        #     cut = ClientData(**args)
        #     expected = parser.parse("20130725T202100-0500")
        #     expected = expected.strftime(self.isoFmt)
        #     self.assertEqual(expected, cut.last_count_update_time())
        # # explicit UTC offset
        # #
        # args = {
        #     "clientId": "What.Ever.Dude",
        #     "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
        #     "lastCountUpdateTime": "Jul 25, 2013 20:21 -05:00"
        # }
        # cut = ClientData(**args)
        # expected = parser.parse("20130725T202100-0500")
        # expected = expected.strftime(self.isoFmt)
        # self.assertEqual(expected, cut.last_count_update_time())

    def test_constructor_last_count_update_time_bad_type(self):
        """Test for __init__().

        Bad value type for last_count_update_time.

        """
        # bad timestamp value
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "lastCountUpdateTime": 12345
        }
        with self.assertRaises(TypeError):
            ClientData(**args)

    def test_constructor_last_count_update_time_bad_value(self):
        """Test for __init__().

        Bad value for last_count_update_time.

        """
        # bad timestamp value
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "lastCountUpdateTime": "abcde"
        }
        with self.assertRaises(iso8601.iso8601.ParseError):
            ClientData(**args)

    def test_constructor_period(self):
        """Test for __init__().

        Happy path period.

        """
        # default
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        cut = ClientData(**args)
        self.assertEqual(30, cut.period())
        # 60
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "period": 60
        }
        cut = ClientData(**args)
        self.assertEqual(60, cut.period())
        # "60"
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "period": "60"
        }
        cut = ClientData(**args)
        self.assertEqual(60, cut.period())
        # default if counter_from_time is False
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "counterFromTime": False
        }
        cut = ClientData(**args)
        self.assertEqual(30, cut.period())

    def test_constructor_period_bad_type(self):
        """Test for __init__().

        Bad value type for period.

        """
        # bad integer value
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "period": (1, 2, 3)
        }
        with self.assertRaises(TypeError):
            ClientData(**args)

    def test_constructor_period_bad_value(self):
        """Test for __init__().

        Bad value for period.

        """
        # out of range value
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "period": -1
        }
        with self.assertRaises(ValueError):
            ClientData(**args)

    def test_constructor_password_length(self):
        """Test for __init__().

        Happy path password length.

        """
        # default
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        cut = ClientData(**args)
        self.assertEqual(6, cut.password_length())
        # 60
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "passwordLength": 1
        }
        cut = ClientData(**args)
        self.assertEqual(1, cut.password_length())
        # "60"
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "passwordLength": "10"
        }
        cut = ClientData(**args)
        self.assertEqual(10, cut.password_length())

    def test_constructor_password_length_bad_type(self):
        """Test for __init__().

        Bad value type for period.

        """
        # bad integer value
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "passwordLength": (1, 2, 3)
        }
        with self.assertRaises(TypeError):
            ClientData(**args)

    def test_constructor_password_length_bad_value(self):
        """Test for __init__().

        Bad value for period.

        """
        # out of range values
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "passwordLength": 0
        }
        with self.assertRaises(ValueError):
            ClientData(**args)
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "passwordLength": 11
        }
        with self.assertRaises(ValueError):
            ClientData(**args)

    def test_constructor_tags(self):
        """Test for __init__().

        Happy path tags.

        """
        # default
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        cut = ClientData(**args)
        self.assertEqual(0, len(cut.tags()))
        # one tag
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "tags": ["this"]
        }
        cut = ClientData(**args)
        self.assertEqual(1, len(cut.tags()))
        self.assertEqual("this", cut.tags()[0])
        # several tags
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "tags": ["this", "that", "those"]
        }
        cut = ClientData(**args)
        self.assertEqual(3, len(cut.tags()))
        self.assertEqual("this", cut.tags()[0])
        self.assertEqual("that", cut.tags()[1])
        self.assertEqual("those", cut.tags()[2])
        # several tags as a tuple
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "tags": ("this", "that", "those")
        }
        cut = ClientData(**args)
        self.assertEqual(3, len(cut.tags()))
        self.assertEqual("this", cut.tags()[0])
        self.assertEqual("that", cut.tags()[1])
        self.assertEqual("those", cut.tags()[2])
        # several tags as a tuple, one empty
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "tags": ("this", "that", "", "those")
        }
        cut = ClientData(**args)
        self.assertEqual(3, len(cut.tags()))
        self.assertEqual("this", cut.tags()[0])
        self.assertEqual("that", cut.tags()[1])
        self.assertEqual("those", cut.tags()[2])
        # one tag as a string
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "tags": "one"
        }
        cut = ClientData(**args)
        self.assertEqual(1, len(cut.tags()))
        self.assertEqual("one", cut.tags()[0])
        # one tag as a tuple
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "tags": ("one")
        }
        cut = ClientData(**args)
        self.assertEqual(1, len(cut.tags()))
        self.assertEqual("one", cut.tags()[0])

    def test_constructor_tags_bad_type(self):
        """Test for __init__().

        Bad value for tags.

        """
        # tags not a collection
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "tags": 0
        }
        with self.assertRaises(TypeError):
            ClientData(**args)

    def test_constructor_note(self):
        """Test for __init__().

        Happy path note.

        """
        # default
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        cut = ClientData(**args)
        self.assertEqual(0, len(cut.note()))
        # one tag
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "note": "What is this thing called love?"
        }
        cut = ClientData(**args)
        self.assertEqual("What is this thing called love?", cut.note())

    def test_constructor_note_bad_type(self):
        """Test for __init__().

        Bad value for note.

        """
        # tags not a collection
        #
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "note": 0
        }
        with self.assertRaises(TypeError):
            ClientData(**args)

    # -------------------------------------------------------------------------
    # Tests for ClientData.__str__()
    # -------------------------------------------------------------------------

    def test_string(self):
        """Test for __string__().

        Happy path test for conversion to string.

        """
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        expected = (
            "client_id: 'What.Ever.Dude'\n"
            "shared_secret: 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'\n"
            "counter_from_time: True\n"
            "last_count: 0\n"
            "last_count_update_time: 00010101T000000+0000\n"
            "period: 30\n"
            "password_length: 6\n"
            "tags: []\n"
            "note: \"\"\"\"\"\"")
        cut = ClientData(**args)
        s = str(cut)
        self.assertEqual(expected, s)

    # -------------------------------------------------------------------------
    # Tests for ClientData.__eq__()
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Tests for ClientData.__ne__()
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Tests for JSON encoding/decoding
    # -------------------------------------------------------------------------

    def test_json_encoding(self):
        """Test for json.dumps() of ClientData object.

        Just trying it out.

        """
        import json

        # Happy path
        #
        expected = self.jsonStringExample01
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        cut = ClientData(**args)
        j = json.dumps(
            cut, sort_keys=True, indent=4, separators=(',', ': '),
            cls=ClientDataEncoder)
        self.assertEqual(expected, j)

    def testjson_decoding(self):
        """Test for json.loads() into a ClientData object.

        Just trying it out.

        """
        import json

        # Happy path
        #
        j = self.jsonStringExample01
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        expected = ClientData(**args)
        cd = json.loads(j, cls=ClientDataDecoder)
        self.assertEqual(expected, cd)

    def test_json_encoding_collection(self):
        """Test for json.dumps() of a list of ClientData objects.

        Just trying it out.

        """
        import json

        # Happy path
        #
        expected = "\n".join((
            "[",
            "    " + "\n    ".join(self.jsonStringExample01.split("\n")) + ",",
            "    " + "\n    ".join(self.jsonStringExample02.split("\n")) + ",",
            "    " + "\n    ".join(self.jsonStringExample03.split("\n")),
            "]"))
        cuts = []
        args = {
            "clientId": "What.Ever.Dude",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
        }
        cuts.append(ClientData(**args))
        args = {
            "clientId": "You.Dont.Say",
            "sharedSecret": "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ",
            "counterFromTime": False,
            "lastCount": 99,
            "lastCountUpdateTime": "20130704T131415-0500",
            "note": "This is not a note.",
            "tags": ["test", "none"]
        }
        cuts.append(ClientData(**args))
        args = {
            "clientId": "Well.I.Never",
            "sharedSecret": "ABCDGNBVGY3TQOJQGEZDGNBVGY3TQCBA",
            "note": "Man who sit on tack better off.",
            "passwordLength": 8,
            "period": 15,
            "tags": ["AWS"]
        }
        cuts.append(ClientData(**args))
        j = json.dumps(
            cuts, sort_keys=True, indent=4, separators=(',', ': '),
            cls=ClientDataEncoder)
        self.assertEqual(expected, j)

    def test_json_decoding_collection(self):
        """Test for json.loads() of a list of ClientData objects.

        Just trying it out.

        """
        import json

        # Happy path
        #
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
        j = "\n".join((
            "[",
            "    " + "\n    ".join(self.jsonStringExample01.split("\n")) + ",",
            "    " + "\n    ".join(self.jsonStringExample02.split("\n")) + ",",
            "    " + "\n    ".join(self.jsonStringExample03.split("\n")),
            "]"))
        cds = json.loads(j, cls=ClientDataDecoder)
        self.assertEqual(expected, cds)
