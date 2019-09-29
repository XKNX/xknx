"""Unit test for KNX binary/integer objects."""
import unittest

from xknx.dpt import DPTArray, DPTBinary, DPTComparator
from xknx.exceptions import ConversionError


class TestDPT(unittest.TestCase):
    """Test class for KNX binary/integer objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_compare_binary(self):
        """Test comparison of DPTBinary objects."""
        self.assertEqual(DPTBinary(0), DPTBinary(0))
        self.assertEqual(DPTBinary(2), DPTBinary(2))
        self.assertNotEqual(DPTBinary(1), DPTBinary(4))
        self.assertNotEqual(DPTBinary(2), DPTBinary(0))
        self.assertNotEqual(DPTBinary(0), DPTBinary(2))

    def test_compare_array(self):
        """Test comparison of DPTArray objects."""
        self.assertEqual(DPTArray(()), DPTArray(()))
        self.assertEqual(DPTArray([1]), DPTArray((1,)))
        self.assertEqual(DPTArray([1, 2, 3]), DPTArray([1, 2, 3]))
        self.assertEqual(DPTArray([1, 2, 3]), DPTArray((1, 2, 3)))
        self.assertEqual(DPTArray((1, 2, 3)), DPTArray([1, 2, 3]))
        self.assertNotEqual(DPTArray((1, 2, 3)), DPTArray([1, 2, 3, 4]))
        self.assertNotEqual(DPTArray((1, 2, 3, 4)), DPTArray([1, 2, 3]))
        self.assertNotEqual(DPTArray((1, 2, 3)), DPTArray([1, 2, 4]))

    def test_compare_none(self):
        """Test comparison of empty DPTArray objects with None."""
        self.assertEqual(DPTArray(()), None)
        self.assertEqual(None, DPTArray(()))
        self.assertEqual(DPTBinary(0), None)
        self.assertEqual(None, DPTBinary(0))
        self.assertNotEqual(DPTArray((1, 2, 3)), None)
        self.assertNotEqual(None, DPTArray((1, 2, 3)))
        self.assertNotEqual(DPTBinary(1), None)
        self.assertNotEqual(None, DPTBinary(1))

    def test_compare_array_binary(self):
        """Test comparison of empty DPTArray objects with DPTBinary objects."""
        self.assertEqual(DPTArray(()), DPTBinary(0))
        self.assertEqual(DPTBinary(0), DPTArray(()))
        self.assertNotEqual(DPTArray((1, 2, 3)), DPTBinary(2))
        self.assertNotEqual(DPTBinary(2), DPTArray((1, 2, 3)))
        self.assertNotEqual(DPTArray((2,)), DPTBinary(2))
        self.assertNotEqual(DPTBinary(2), DPTArray((2,)))

    def test_dpt_binary_assign(self):
        """Test initialization of DPTBinary objects."""
        self.assertEqual(DPTBinary(8).value, 8)

    def test_dpt_binary_assign_limit_exceeded(self):
        """Test initialization of DPTBinary objects with wrong value (value exceeded)."""
        with self.assertRaises(ConversionError):
            DPTBinary(DPTBinary.APCI_MAX_VALUE + 1)

    def test_dpt_init_with_string(self):
        """Teest initialization of DPTBinary object with wrong value (wrong type)."""
        with self.assertRaises(TypeError):
            DPTBinary("bla")

    def test_dpt_array_init_with_string(self):
        """Test initialization of DPTArray object with wrong value (wrong type)."""
        with self.assertRaises(TypeError):
            DPTArray("bla")

    def test_dpt_comparator_none_with_none(self):
        """Test comperator for DPTBinary and DPTBinary - missing cases."""
        self.assertTrue(DPTComparator.compare(None, None))
        self.assertTrue(DPTComparator.compare(None, DPTBinary(0)))
        self.assertTrue(DPTComparator.compare(None, DPTArray(())))

    def test_dpt_comparator_none_with_wrong_parameter(self):
        """Test comperator for DPTBinary and DPTBinary - wrong parameter."""
        with self.assertRaises(TypeError):
            DPTComparator.compare("bla", DPTBinary(0))
