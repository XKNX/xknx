import unittest

from xknx import Address, AddressType, CouldNotParseAddress

class TestAddress(unittest.TestCase):

    #
    # INIT
    #
    def test_address_init_3level(self):
        self.assertEqual( Address("2.3.4").raw, 8964 )

    def test_address_init_2level(self):
        self.assertEqual( Address("12.500").raw, 49652 )

    def test_address_init_free(self):
        self.assertEqual( Address("49552").raw, 49552 )

    def test_address_init_int(self):
        self.assertEqual( Address(49552).raw, 49552 )

    def test_address_init_address(self):
        self.assertEqual( Address(Address("2.3.4")).raw, 8964 )


    #
    # ADDRESS TYPE
    #
    def test_address_type_3level(self):
        self.assertEqual( Address("2.3.4").address_type, AddressType.LEVEL3 )

    def test_address_type_2level(self):
        self.assertEqual( Address("12.500").address_type, AddressType.LEVEL2 )

    def test_address_type_free(self):
        self.assertEqual( Address("49552").address_type, AddressType.FREE )

    def test_address_type_int(self):
        self.assertEqual( Address(49552).address_type, AddressType.FREE )

    def test_address_type_address(self):
        self.assertEqual( Address(Address("2.3.4")).address_type, AddressType.LEVEL3 )

    #
    # STR
    #
    def test_address_str_3level(self):
        self.assertEqual( Address("2.3.4").__str__(), "2.3.4" )

    def test_address_str_2level(self):
        self.assertEqual( Address("12.500").__str__(), "12.500" )

    def test_address_str_free(self):
        self.assertEqual( Address("49552").__str__(), "49552" )

    def test_address_str_int(self):
        self.assertEqual( Address(49552).__str__(), "49552" )

    def test_address_str_address(self):
        self.assertEqual( Address(Address("2.3.4")).__str__(), "2.3.4" )

    #
    # MAXIMUM ADDRESSES
    #
    def test_address_max_3level(self):
        self.assertEqual( Address("15.15.255").raw, 65535 )

    def test_address_max_2level(self):
        self.assertEqual( Address("15.4095").raw, 65535 )

    def test_address_max_free(self):
        self.assertEqual( Address("65535").raw, 65535 )

    def test_address_max_int(self):
        self.assertEqual( Address(65535).raw, 65535 )

    def test_address_max_address(self):
        self.assertEqual( Address(Address("15.15.255")).raw, 65535 )


    #
    # INVALID INIT STRINGS
    #
    def test_address_init_failed_too_many_parts(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("1.2.3.4")

    def test_address_init_failed_string(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("bla123")

    def test_address_init_failed_string_part(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("1.2.3a")

    def test_address_init_failed_level3_boundaries_sub(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("1.2.256")

    def test_address_init_failed_level3_boundaries_middle(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("1.16.3")

    def test_address_init_failed_level3_boundaries_main(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("16.2.3")

    def test_address_init_failed_level2_boundaries_sub(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("1.4096")

    def test_address_init_failed_level2_boundaries_middle(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("16.3")

    def test_address_init_failed_free_boundaries(self):
        with self.assertRaises(CouldNotParseAddress):
            Address("65536")

    #
    # __eq__
    #
    def test_address_equal(self):
         self.assertTrue( Address("2.3.4") == Address("2.3.4") )

    def test_address_equal_false(self):
        self.assertFalse( Address("2.3.4") == Address("2.3.5") )

    def test_address_not_equal(self):
         self.assertTrue( Address("2.3.4") != Address("2.3.5") )

    def test_address_not_qual_false(self):
         self.assertFalse( Address("2.3.4") != Address("2.3.4") )

    def test_address_equal_diffent_source(self):
        self.assertTrue( Address("2.3.4") == Address("2.772") )

    #
    # BYTE ACCESS
    #
    def test_address_byte1(self):
            self.assertEqual( Address("2.3.100").byte1(), 2*16+3 )

    def test_address_byte2(self):
            self.assertEqual( Address("2.3.100").byte2(), 100 )


suite = unittest.TestLoader().loadTestsFromTestCase(TestAddress)
unittest.TextTestRunner(verbosity=2).run(suite)
