import unittest

from xknx.knx import Address, AddressFormat, AddressType, CouldNotParseAddress

class TestAddress(unittest.TestCase):
    # pylint: disable=too-many-public-methods,invalid-name

    #
    # INIT
    #
    def test_address_init_3level(self):
        self.assertEqual(Address("2/3/4").raw, 2*2048 + 3*256 + 4)

    def test_address_init_2level(self):
        self.assertEqual(Address("12/500").raw, 12*2048 + 500)

    def test_address_init_free(self):
        self.assertEqual(Address("49552").raw, 49552)

    def test_address_init_int(self):
        self.assertEqual(Address(49552).raw, 49552)

    def test_address_init_bytes(self):
        self.assertEqual(Address((0x12, 0x34)).raw, 0x1234)

    def test_address_init_address(self):
        self.assertEqual(Address(Address("2/3/4")).raw, 2*2048 + 3*256 + 4)

    def test_address_init_none(self):
        self.assertEqual(Address(None).raw, 0)

    def test_address_init_address_physical(self):
        address = Address("2.3.4", AddressType.PHYSICAL)
        self.assertEqual(Address(address).raw, 8964)


    #
    # ADDRESS FORMAT
    #
    def test_address_format_3level(self):
        self.assertEqual(
            Address("2/3/4").address_format,
            AddressFormat.LEVEL3)

    def test_address_format_2level(self):
        self.assertEqual(
            Address("12/500").address_format,
            AddressFormat.LEVEL2)

    def test_address_format_free(self):
        self.assertEqual(
            Address("49552").address_format,
            AddressFormat.FREE)

    def test_address_format_int(self):
        self.assertEqual(
            Address(49552).address_format,
            AddressFormat.FREE)

    def test_address_format_address(self):
        self.assertEqual(
            Address(Address("2/3/4")).address_format,
            AddressFormat.LEVEL3)

    #
    # ADDRESS TYPE
    #
    def test_address_type_physical(self):
        self.assertEqual(
            Address("2.3.4", AddressType.PHYSICAL).address_type,
            AddressType.PHYSICAL)

    def test_address_type_physical_auto_detect(self):
        self.assertEqual(
            Address("2.3.4").address_type,
            AddressType.PHYSICAL)

    def test_address_type_group(self):
        self.assertEqual(
            Address("2/3/4").address_type,
            AddressType.GROUP)

    #
    # STR
    #
    def test_address_str_3level(self):
        self.assertEqual(
            Address("2/3/4").str(),
            "2/3/4")

    def test_address_str_2level(self):
        self.assertEqual(
            Address("12/500").str(),
            "12/500")

    def test_address_str_free(self):
        self.assertEqual(
            Address("49552").str(),
            "49552")

    def test_address_str_int(self):
        self.assertEqual(
            Address(49552).str(),
            "49552")

    def test_address_str_address(self):
        self.assertEqual(
            Address(Address("2/3/4")).str(),
            "2/3/4")

    def test_address_str_physical(self):
        self.assertEqual(
            Address("2.3.4", AddressType.PHYSICAL).str(),
            "2.3.4")

    #
    # MAXIMUM ADDRESSES
    #
    def test_address_max_3level(self):
        self.assertEqual(Address("31/7/255").raw, 65535)

    def test_address_max_2level(self):
        self.assertEqual(Address("31/2047").raw, 65535)

    def test_address_max_free(self):
        self.assertEqual(Address("65535").raw, 65535)

    def test_address_max_int(self):
        self.assertEqual(Address(65535).raw, 65535)

    def test_address_max_address(self):
        self.assertEqual(Address(Address("31/7/255")).raw, 65535)


    #
    # INVALID INIT STRINGS
    #
    def test_address_init_failed_too_many_parts(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("1/2/3/4")

    def test_address_init_failed_string(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("bla123")

    def test_address_init_failed_string_part(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("1/2/3a")

    def test_address_init_failed_level3_boundaries_sub(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("1/2/256")

    def test_address_init_failed_level3_boundaries_middle(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("1/8/3")

    def test_address_init_failed_level3_boundaries_main(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("32/2/3")

    def test_address_init_failed_level2_boundaries_sub(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("1.4096")

    def test_address_init_failed_level2_boundaries_middle(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("16.3")

    def test_address_init_failed_free_boundaries(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("65536")

    def test_address_init_empty_string(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("")

    def test_address_init_tuple_3_elements(self):
        with self.assertRaises(CouldNotParseAddress):
            Address((1, 2, 3))

    def test_address_init_tuple_string(self):
        with self.assertRaises(CouldNotParseAddress):
            Address((2, "23"))

    def test_address_init_tuple_range_overflow(self):
        with self.assertRaises(CouldNotParseAddress):
            Address((4, 256))

    def test_address_init_tuple_range_underflow(self):
        with self.assertRaises(CouldNotParseAddress):
            Address((1, -1))

    #
    # __eq__
    #
    def test_address_equal(self):
        self.assertTrue(Address("2/3/4") == Address("2/3/4"))

    def test_address_equal_false(self):
        self.assertFalse(Address("2/3/4") == Address("2/3/5"))

    def test_address_not_equal(self):
        self.assertTrue(Address("2/3/4") != Address("2/3/5"))

    def test_address_not_qual_false(self):
        self.assertFalse(Address("2/3/4") != Address("2/3/4"))

    def test_address_equal_diffent_source(self):
        self.assertTrue(Address("2/3/4") == Address("2/772"))

    #
    # TO KNX
    #

    def test_address_to_knx(self):
        self.assertEqual(Address("2/3/100").to_knx(), (2*8+3, 100))


SUITE = unittest.TestLoader().loadTestsFromTestCase(TestAddress)
unittest.TextTestRunner(verbosity=2).run(SUITE)
