"""Unit test for Address class."""
import unittest

from xknx.exceptions import ConversionError
from xknx.telegram import AddressFilter, GroupAddress


class TestAddressFilter(unittest.TestCase):
    """Test class for Address."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_range_initialization(self):
        """Test Initialization of AddresFilter.Range."""
        self.assertEqual(AddressFilter.Range("*").get_range(), (0, 65535))
        self.assertEqual(AddressFilter.Range("5").get_range(), (5, 5))
        self.assertEqual(AddressFilter.Range("0").get_range(), (0, 0))
        self.assertEqual(AddressFilter.Range("3-5").get_range(), (3, 5))
        self.assertEqual(AddressFilter.Range("5-3").get_range(), (3, 5))
        self.assertEqual(AddressFilter.Range("-5").get_range(), (0, 5))
        self.assertEqual(AddressFilter.Range("5-").get_range(), (5, 65535))
        self.assertEqual(AddressFilter.Range("70-100").get_range(), (70, 100))

    def test_range_test(self):
        """Test matching within AddressFilter.Range."""
        rf = AddressFilter.Range("2-16")
        self.assertTrue(rf.match(10))
        self.assertTrue(rf.match(2))
        self.assertTrue(rf.match(16))
        self.assertFalse(rf.match(1))
        self.assertFalse(rf.match(17))

    def test_level_filter_test(self):
        """Test matching within AddressFilter.LevelFilter."""
        lf = AddressFilter.LevelFilter("2,4,8-10,13")
        self.assertFalse(lf.match(1))
        self.assertTrue(lf.match(2))
        self.assertFalse(lf.match(3))
        self.assertTrue(lf.match(4))
        self.assertFalse(lf.match(5))
        self.assertTrue(lf.match(9))

    def test_address_filter_level3_3(self):
        """Test AddressFilter 3rd part of level3 addresses."""
        af1 = AddressFilter("1/2/3")
        self.assertTrue(af1.match("1/2/3"))
        self.assertFalse(af1.match("1/2/4"))
        self.assertFalse(af1.match("1/2/1"))
        af2 = AddressFilter("1/2/2-3,5-")
        self.assertFalse(af2.match("1/2/1"))
        self.assertTrue(af2.match("1/2/3"))
        self.assertFalse(af2.match("1/2/4"))
        self.assertTrue(af2.match("1/2/6"))
        af3 = AddressFilter("1/2/*")
        self.assertTrue(af3.match("1/2/3"))
        self.assertTrue(af3.match("1/2/5"))

    def test_address_filter_level3_2(self):
        """Test AddressFilter 2nd part of level3 addresses."""
        af1 = AddressFilter("1/2/3")
        self.assertTrue(af1.match("1/2/3"))
        self.assertFalse(af1.match("1/3/3"))
        self.assertFalse(af1.match("1/1/3"))
        af2 = AddressFilter("1/2-/3")
        self.assertFalse(af2.match("1/1/3"))
        self.assertTrue(af2.match("1/2/3"))
        self.assertTrue(af2.match("1/5/3"))
        af3 = AddressFilter("1/*/3")
        self.assertTrue(af3.match("1/4/3"))
        self.assertTrue(af3.match("1/7/3"))

    def test_address_filter_level3_1(self):
        """Test AddressFilter 1st part of level3 addresses."""
        af1 = AddressFilter("4/2/3")
        self.assertTrue(af1.match("4/2/3"))
        self.assertFalse(af1.match("2/2/3"))
        self.assertFalse(af1.match("10/2/3"))
        af2 = AddressFilter("2-/4/3")
        self.assertFalse(af2.match("1/4/3"))
        self.assertTrue(af2.match("2/4/3"))
        self.assertTrue(af2.match("10/4/3"))
        af3 = AddressFilter("*/5/5")
        self.assertTrue(af3.match("2/5/5"))
        self.assertTrue(af3.match("8/5/5"))

    def test_address_filter_level2_2(self):
        """Test AddressFilter 2nd part of level2 addresses."""
        af1 = AddressFilter("2/3")
        self.assertTrue(af1.match("2/3"))
        self.assertFalse(af1.match("2/4"))
        self.assertFalse(af1.match("2/1"))
        af2 = AddressFilter("2/3-4,7-")
        self.assertFalse(af2.match("2/2"))
        self.assertTrue(af2.match("2/3"))
        self.assertFalse(af2.match("2/6"))
        self.assertTrue(af2.match("2/8"))
        af3 = AddressFilter("2/*")
        self.assertTrue(af3.match("2/3"))
        self.assertTrue(af3.match("2/5"))

    def test_address_filter_level2_1(self):
        """Test AddressFilter 1st part of level2 addresses."""
        af1 = AddressFilter("4/2")
        self.assertTrue(af1.match("4/2"))
        self.assertFalse(af1.match("2/2"))
        self.assertFalse(af1.match("10/2"))
        af2 = AddressFilter("2-3,8-/4")
        self.assertFalse(af2.match("1/4"))
        self.assertTrue(af2.match("2/4"))
        self.assertFalse(af2.match("7/4"))
        self.assertTrue(af2.match("10/4"))
        af3 = AddressFilter("*/5")
        self.assertTrue(af3.match("2/5"))
        self.assertTrue(af3.match("8/5"))

    def test_address_filter_free(self):
        """Test AddressFilter free format addresses."""
        af1 = AddressFilter("4")
        self.assertTrue(af1.match("4"))
        self.assertFalse(af1.match("1"))
        self.assertFalse(af1.match("10"))
        af2 = AddressFilter("1,4,7-")
        self.assertTrue(af2.match("1"))
        self.assertFalse(af2.match("2"))
        self.assertTrue(af2.match("4"))
        self.assertFalse(af2.match("6"))
        self.assertTrue(af2.match("60"))
        af3 = AddressFilter("*")
        self.assertTrue(af3.match("2"))
        self.assertTrue(af3.match("8"))

    def test_address_combined(self):
        """Test AddressFilter with complex filters."""
        af1 = AddressFilter("2-/2,3,5-/*")
        self.assertTrue(af1.match("2/3/8"))
        self.assertTrue(af1.match("4/7/10"))
        self.assertTrue(af1.match("2/7/10"))
        self.assertFalse(af1.match("1/7/10"))
        self.assertFalse(af1.match("2/4/10"))
        self.assertFalse(af1.match("2/1/10"))

    def test_initialize_wrong_format(self):
        """Test if wrong address format raises exception."""
        with self.assertRaises(ConversionError):
            AddressFilter("2-/2,3/4/5/1,5-/*")

    def test_adjust_range(self):
        """Test helper function _adjust_range."""
        # pylint: disable=protected-access
        self.assertEqual(AddressFilter.Range._adjust_range(GroupAddress.MAX_FREE+1), GroupAddress.MAX_FREE)
        self.assertEqual(AddressFilter.Range._adjust_range(-1), 0)
