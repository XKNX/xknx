"""Unit test for Address class."""
from unittest import TestCase

from xknx.exceptions import CouldNotParseAddress
from xknx.telegram import GroupAddress, GroupAddressType, PhysicalAddress


class TestPhysicalAddress(TestCase):
    """Test class for PhysicalAddress."""

    def test_with_valid(self):
        """Test with some valid addresses."""
        valid_addresses = (
            ('0.0.0', 0),
            ('1.0.0', 4096),
            ('1.1.0', 4352),
            ('1.1.1', 4353),
            ('1.1.11', 4363),
            ('1.1.111', 4463),
            ('1.11.111', 7023),
            ('11.11.111', 47983),
            ('15.15.255', 65535),
            ((0xff, 0xff), 65535),
            (0, 0),
            (65535, 65535)
        )
        for address in valid_addresses:
            with self.subTest(address=address):
                self.assertEqual(PhysicalAddress(address[0]).raw, address[1])

    def test_with_invalid(self):
        """Test with some invalid addresses."""
        invalid_addresses = (
            '15.15.256',
            '16.0.0',
            '0.16.0',
            '15.15.255a',
            'a15.15.255',
            'abc',
            '123',
            65536,
            (0xff, 0xfff),
            (0xfff, 0xff),
            (-1, -1),
            []
        )
        for address in invalid_addresses:
            with self.subTest(address=address):
                with self.assertRaises(CouldNotParseAddress):
                    PhysicalAddress(address)

    def test_with_int(self):
        """Test initialization with free format address as integer."""
        self.assertEqual(PhysicalAddress(49552).raw, 49552)

    def test_with_bytes(self):
        """Test initialization with Bytes."""
        self.assertEqual(PhysicalAddress((0x12, 0x34)).raw, 0x1234)

    def test_with_none(self):
        """Test initialization with None object."""
        self.assertEqual(PhysicalAddress(None).raw, 0)

    def test_is_line(self):
        """Test if `PhysicalAddress.is_line` works like excepted."""
        self.assertTrue(PhysicalAddress('1.0.0').is_line)
        self.assertFalse(PhysicalAddress('1.0.1').is_line)

    def test_is_device(self):
        """Test if `PhysicalAddress.is_device` works like excepted."""
        self.assertTrue(PhysicalAddress('1.0.1').is_device)
        self.assertFalse(PhysicalAddress('1.0.0').is_device)

    def test_to_knx(self):
        """Test if `PhysicalAddress.to_knx()` generates valid byte tuples."""
        self.assertEqual(PhysicalAddress('0.0.0').to_knx(), (0x0, 0x0))
        self.assertEqual(PhysicalAddress('15.15.255').to_knx(), (0xff, 0xff))

    def test_equal(self):
        """Test if the equal operator works in all cases."""
        self.assertEqual(PhysicalAddress('1.0.0'), PhysicalAddress(4096))
        self.assertNotEqual(PhysicalAddress('1.0.0'), PhysicalAddress('1.1.1'))
        self.assertNotEqual(PhysicalAddress('1.0.0'), None)
        with self.assertRaises(TypeError):
            PhysicalAddress('1.0.0') == 'example'  # pylint: disable=expression-not-assigned

    def test_representation(self):
        """Test string representation of address."""
        self.assertEqual(
            repr(PhysicalAddress("2.3.4")),
            'PhysicalAddress("2.3.4")')


class TestGroupAddress(TestCase):
    """Test class for GroupAddress."""

    def test_with_valid(self):
        """
        Test if the class constructor generates valid raw values.

        This test checks:
        * all allowed input variants (strings, tuples, integers)
        * for conversation errors
        * for upper/lower limits still working, to avoid off-by-one errors
        """
        valid_addresses = (
            ('0/0', 0),
            ('0/1', 1),
            ('0/11', 11),
            ('0/111', 111),
            ('0/1111', 1111),
            ('0/2047', 2047),
            ('0/0/0', 0),
            ('0/0/1', 1),
            ('0/0/11', 11),
            ('0/0/111', 111),
            ('0/0/255', 255),
            ('0/1/11', 267),
            ('0/1/111', 367),
            ('0/7/255', 2047),
            ('1/0', 2048),
            ('1/0/0', 2048),
            ('1/1/111', 2415),
            ('1/7/255', 4095),
            ('31/7/255', 65535),
            ('1', 1),
            (0, 0),
            (65535, 65535),
            ((0xff, 0xff), 65535),
            (None, 0)
        )
        for address in valid_addresses:
            with self.subTest(address=address):
                self.assertEqual(GroupAddress(address[0]).raw, address[1])

    def test_with_invalid(self):
        """
        Test if constructor raises an exception for all known invalid cases.

        Checks:
        * addresses or parts of it too high/low
        * invalid input variants (lists instead of tuples)
        * invalid strings
        """
        invalid_addresses = (
            '0/2049',
            '0/8/0',
            '0/0/256',
            '32/0',
            '0/0a',
            'a0/0',
            'abc',
            65536,
            (0xff, 0xfff),
            (0xfff, 0xff),
            (-1, -1),
            []
        )
        for address in invalid_addresses:
            with self.subTest(address=address):
                with self.assertRaises(CouldNotParseAddress):
                    GroupAddress(address)

    def test_main(self):
        """
        Test if `GroupAddress.main` works.

        Checks:
        * Main group part of a strings returns the right value
        * Return `None` on `GroupAddressType.FREE`
        """
        self.assertEqual(GroupAddress('1/0').main, 1)
        self.assertEqual(GroupAddress('15/0').main, 15)
        self.assertEqual(GroupAddress('31/0/0').main, 31)
        self.assertIsNone(GroupAddress('1/0', GroupAddressType.FREE).main)

    def test_middle(self):
        """
        Test if `GroupAddress.middle` works.

        Checks:
        * Middle group part of a strings returns the right value
        * Return `None` if not `GroupAddressType.LONG`
        """
        self.assertEqual(GroupAddress('1/0/1', GroupAddressType.LONG).middle, 0)
        self.assertEqual(GroupAddress('1/7/1', GroupAddressType.LONG).middle, 7)
        self.assertIsNone(GroupAddress('1/0', GroupAddressType.SHORT).middle)
        self.assertIsNone(GroupAddress('1/0', GroupAddressType.FREE).middle)

    def test_sub(self):
        """
        Test if `GroupAddress.sub` works.

        Checks:
        * Sub group part of a strings returns the right value
        * Return never `None`
        """
        self.assertEqual(GroupAddress('1/0', GroupAddressType.SHORT).sub, 0)
        self.assertEqual(GroupAddress('31/0', GroupAddressType.SHORT).sub, 0)
        self.assertEqual(GroupAddress('1/2047', GroupAddressType.SHORT).sub, 2047)
        self.assertEqual(GroupAddress('31/2047', GroupAddressType.SHORT).sub, 2047)
        self.assertEqual(GroupAddress('1/0/0', GroupAddressType.LONG).sub, 0)
        self.assertEqual(GroupAddress('1/0/255', GroupAddressType.LONG).sub, 255)
        self.assertEqual(GroupAddress('0/0', GroupAddressType.FREE).sub, 0)
        self.assertEqual(GroupAddress('1/0', GroupAddressType.FREE).sub, 2048)
        self.assertEqual(GroupAddress('31/2047', GroupAddressType.FREE).sub, 65535)

    def test_to_knx(self):
        """Test if `GroupAddress.to_knx()` generates valid byte tuples."""
        self.assertEqual(GroupAddress('0/0').to_knx(), (0x0, 0x0))
        self.assertEqual(GroupAddress('31/2047').to_knx(), (0xff, 0xff))

    def test_equal(self):
        """Test if the equal operator works in all cases."""
        self.assertEqual(GroupAddress('1/0'), GroupAddress(2048))
        self.assertNotEqual(GroupAddress('1/1'), GroupAddress('1/1/0'))
        self.assertNotEqual(GroupAddress('1/0'), None)
        with self.assertRaises(TypeError):
            GroupAddress('1/0') == 'example'  # pylint: disable=expression-not-assigned

    def test_representation(self):
        """Test string representation of address."""
        self.assertEqual(
            repr(GroupAddress('0', GroupAddressType.FREE)),
            'GroupAddress("0")'
        )
        self.assertEqual(
            repr(GroupAddress('0', GroupAddressType.SHORT)),
            'GroupAddress("0/0")'
        )
        self.assertEqual(
            repr(GroupAddress('0', GroupAddressType.LONG)),
            'GroupAddress("0/0/0")'
        )
