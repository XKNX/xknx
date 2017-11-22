"""Unit test for KNX Groups and related stuff."""
from unittest import TestCase

from xknx.knx.groups import is_group


class TestGroupsTools(TestCase):
    """Test class for all group tools."""

    def test_is_group_with_string(self):
        """
        Test is_group with strings as input.

        Test some basic string examples agains is_group. A empty string is
        never a valid group address.
        """
        self.assertEqual(is_group('Example'), True)
        self.assertEqual(is_group('1/0/0'), True)
        self.assertEqual(is_group('1/0'), True)
        self.assertEqual(is_group(''), False)

    def test_is_group_with_integer(self):
        """
        Test is_group with integers as input.

        KNX Groups have an allowed range between 1-65536, all other integers
        are invalid.
        """
        self.assertEqual(is_group(0), False)
        self.assertEqual(is_group(65537), False)
        self.assertEqual(is_group(123), True)

    def test_is_group_with_float(self):
        """
        Test is_group with floats as input.

        KNX Groups can be represented as integer, hex or string, but never as
        float.
        """
        self.assertEqual(is_group(1.123), False)

    def test_is_group_with_none(self):
        """
        Test is_group with None as input.

        Test if is_group(None) returns False.
        """
        self.assertEqual(is_group(None), False)

    def test_is_group_with_boolean(self):
        """
        Test is_group with boolean as input.

        Boolean representation of KNX Groups make no sense.
        """
        self.assertEqual(is_group(True), False)
        self.assertEqual(is_group(False), False)
