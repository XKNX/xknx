"""Unit test for Address class."""
import unittest

from xknx.knx import Address, AddressFormat, AddressType
from xknx.exceptions import CouldNotParseAddress

class TestAddress(unittest.TestCase):
    """Test class for Address."""

    # pylint: disable=too-many-public-methods,invalid-name

    #
    # INIT
    #
    def test_address_init_3level(self):
        """Test initialization with 3rd level address."""
        self.assertEqual(Address("2/3/4").raw, 2*2048 + 3*256 + 4)

    def test_address_init_2level(self):
        """Test initialization with 2nd level address."""
        self.assertEqual(Address("12/500").raw, 12*2048 + 500)

    def test_address_init_free(self):
        """Test initialization with free format address as string."""
        self.assertEqual(Address("49552").raw, 49552)

    def test_address_init_int(self):
        """Test initialization with free format address as integer."""
        self.assertEqual(Address(49552).raw, 49552)

    def test_address_init_bytes(self):
        """Test initialization with Bytes."""
        self.assertEqual(Address((0x12, 0x34)).raw, 0x1234)

    def test_address_init_address(self):
        """Test initialization with Address object."""
        self.assertEqual(Address(Address("2/3/4")).raw, 2*2048 + 3*256 + 4)

    def test_address_init_none(self):
        """Test initialization with None object."""
        self.assertEqual(Address(None).raw, 0)

    def test_address_init_address_physical(self):
        """Test inialization with Physical Address."""
        address = Address("2.3.4", AddressType.PHYSICAL)
        self.assertEqual(Address(address).raw, 8964)

    def test_address_format_3level(self):
        """Test address_format of 3rd level Address."""
        self.assertEqual(
            Address("2/3/4").address_format,
            AddressFormat.LEVEL3)

    def test_address_format_2level(self):
        """Test address_format of 2nd level Address."""
        self.assertEqual(
            Address("12/500").address_format,
            AddressFormat.LEVEL2)

    def test_address_format_free(self):
        """Test address_format of free format Address."""
        self.assertEqual(
            Address("49552").address_format,
            AddressFormat.FREE)

    def test_address_format_int(self):
        """Test address_format of Address initalized by int."""
        self.assertEqual(
            Address(49552).address_format,
            AddressFormat.LEVEL3)

    def test_address_format_address(self):
        """Test address_format of Address initialized by Address."""
        self.assertEqual(
            Address(Address("2/3/4")).address_format,
            AddressFormat.LEVEL3)

    #
    # ADDRESS TYPE
    #
    def test_address_type_physical(self):
        """Test address_type of physical Address."""
        self.assertEqual(
            Address("2.3.4", AddressType.PHYSICAL).address_type,
            AddressType.PHYSICAL)

    def test_address_type_physical_auto_detect(self):
        """Test address_type of pyhsical Address (via autodetect)."""
        self.assertEqual(
            Address("2.3.4").address_type,
            AddressType.PHYSICAL)

    def test_address_type_group(self):
        """Test address_type of group address."""
        self.assertEqual(
            Address("2/3/4").address_type,
            AddressType.GROUP)

    #
    # STR
    #
    def test_address_str_3level(self):
        """Test string representation of 3rd level group address."""
        self.assertEqual(
            Address("2/3/4").str(),
            "2/3/4")

    def test_address_str_2level(self):
        """Test string representation of 2nd level group address."""
        self.assertEqual(
            Address("12/500").str(),
            "12/500")

    def test_address_str_free(self):
        """Test string representation of free format group address."""
        self.assertEqual(
            Address("49552").str(),
            "49552")

    def test_address_str_int(self):
        """Test string representation of address initialized by int."""
        self.assertEqual(
            Address(49552).str(),
            "24/1/144")

    def test_address_str_address(self):
        """Test string representation of address initialized by Address object."""
        self.assertEqual(
            Address(Address("2/3/4")).str(),
            "2/3/4")

    def test_address_str_physical(self):
        """Test string representation of physical address."""
        self.assertEqual(
            Address("2.3.4", AddressType.PHYSICAL).str(),
            "2.3.4")

    #
    # MAXIMUM ADDRESSES
    #
    def test_address_max_3level(self):
        """Test initialization of Address with maximum 3rd level address."""
        self.assertEqual(Address("31/7/255").raw, 65535)

    def test_address_max_2level(self):
        """Test initialization of Address with maximum 2nd level address."""
        self.assertEqual(Address("31/2047").raw, 65535)

    def test_address_max_free(self):
        """Test initialization of Address with maximum free format address."""
        self.assertEqual(Address("65535").raw, 65535)

    def test_address_max_int(self):
        """Test initialization of Address with max int."""
        self.assertEqual(Address(65535).raw, 65535)

    def test_address_max_address(self):
        """Test initialization of Address with maximum Address."""
        self.assertEqual(Address(Address("31/7/255")).raw, 65535)


    #
    # INVALID INIT STRINGS
    #
    def test_address_init_failed_too_many_parts(self):
        """Test initialization of Address with invalid string."""
        with self.assertRaises(CouldNotParseAddress):
            Address("1/2/3/4")

    def test_address_init_failed_string(self):
        """Test initialization of Address with invalid string."""
        with self.assertRaises(CouldNotParseAddress):
            Address("bla123")

    def test_address_init_failed_string_part(self):
        """Test initialization of Address with invalid string."""
        with self.assertRaises(CouldNotParseAddress):
            Address("1/2/3a")

    def test_address_init_failed_level3_boundaries_sub(self):
        """Test initialization of 3rd level Address with invalid number value at the end."""
        with self.assertRaises(CouldNotParseAddress):
            Address("1/2/256")

    def test_address_init_failed_level3_boundaries_middle(self):
        """Test initialization of 3rd level Address with invalid number value in the middle."""
        with self.assertRaises(CouldNotParseAddress):
            Address("1/8/3")

    def test_address_init_failed_level3_boundaries_main(self):
        """Test initialization of 3rd level Address with invalid number value at the beginning."""
        with self.assertRaises(CouldNotParseAddress):
            Address("32/2/3")

    def test_address_init_failed_level2_boundaries_sub(self):
        """Test initialization of 2rd level Address with invalid number value at the end."""
        with self.assertRaises(CouldNotParseAddress):
            Address("1.4096")

    def test_address_init_failed_level2_boundaries_middle(self):
        """Test initialization of 2rd level Address with invalid number value at the beginning."""
        with self.assertRaises(CouldNotParseAddress):
            Address("16.3")

    def test_address_init_failed_free_boundaries(self):
        """Test initialization of free format Address with invalid number value."""
        with self.assertRaises(CouldNotParseAddress):
            Address("65536")

    def test_address_init_empty_string(self):
        """Test initialization of Address with invalid empty string."""
        with self.assertRaises(CouldNotParseAddress):
            Address("")

    def test_address_init_tuple_3_elements(self):
        """Test initialization of Address with invalid tuple."""
        with self.assertRaises(CouldNotParseAddress):
            Address((1, 2, 3))

    def test_address_init_tuple_string(self):
        """Test initialization of Address with invalid tuple string."""
        with self.assertRaises(CouldNotParseAddress):
            Address((2, "23"))

    def test_address_init_tuple_range_overflow(self):
        """Test initialization of Address with tuple with invalid 2nd value."""
        with self.assertRaises(CouldNotParseAddress):
            Address((4, 256))

    def test_address_init_tuple_range_underflow(self):
        """Test initialization of Address with tuple with invalid 1st value."""
        with self.assertRaises(CouldNotParseAddress):
            Address((1, -1))

    #
    # __eq__
    #
    def test_address_equal(self):
        """Test equals operator with equal objects."""
        self.assertTrue(Address("2/3/4") == Address("2/3/4"))

    def test_address_equal_false(self):
        """Test equals operator with non equal objects."""
        self.assertFalse(Address("2/3/4") == Address("2/3/5"))

    def test_address_not_equal(self):
        """Test non equals operator with non equal objects."""
        self.assertTrue(Address("2/3/4") != Address("2/3/5"))

    def test_address_not_qual_false(self):
        """Test not equals operator with equal object."""
        self.assertFalse(Address("2/3/4") != Address("2/3/4"))

    def test_address_equal_diffent_source(self):
        """Test equals operator. Different format should not have relevance for the equality."""
        self.assertTrue(Address("2/3/4") == Address("2/772"))

    #
    # TO KNX
    #

    def test_address_to_knx(self):
        """Test to_knx functionality of Address object."""
        self.assertEqual(Address("2/3/100").to_knx(), (2*8+3, 100))


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestAddress)
unittest.TextTestRunner(verbosity=2).run(SUITE)
