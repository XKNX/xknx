"""Unit test for KNX binary/integer objects."""
import unittest

from xknx.dpt import DPTArray, DPTBinary, DPTComparator, DPTTranscoder
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


class TestDPTTranscoder(unittest.TestCase):
    """Test class for transcoder base object."""

    def test_dpt_subclasses_definition_types(self):
        """Test value_type and dpt_*_number values for correct type in subclasses of DPTTranscoder."""
        for dpt in DPTTranscoder.__recursive_subclasses__():
            if hasattr(dpt, 'value_type'):
                self.assertTrue(isinstance(dpt.value_type, str),
                                msg="Wrong type for value_type in %s - str expected" % dpt)
            if hasattr(dpt, 'dpt_main_number'):
                self.assertTrue(isinstance(dpt.dpt_main_number, int),
                                msg="Wrong type for dpt_main_number in %s - int expected" % dpt)
            if hasattr(dpt, 'dpt_sub_number'):
                self.assertTrue(isinstance(dpt.dpt_sub_number, (int, type(None))),
                                msg="Wrong type for dpt_sub_number in %s - int or `None` expected" % dpt)

    def test_dpt_subclasses_no_duplicate_value_types(self):
        """Test for duplicate value_type values in subclasses of DPTTranscoder."""
        value_types = []
        for dpt in DPTTranscoder.__recursive_subclasses__():
            if hasattr(dpt, 'value_type'):
                value_types.append(dpt.value_type)
        self.assertCountEqual(value_types,
                              set(value_types))

    def test_dpt_subclasses_have_both_dpt_number_attributes(self):
        """Test DPTTranscoder subclasses for having both dpt number attributes set."""
        for dpt in DPTTranscoder.__recursive_subclasses__():
            if hasattr(dpt, 'dpt_main_number'):
                self.assertTrue(hasattr(dpt, 'dpt_sub_number'),
                                "No dpt_sub_number in %s" % dpt)

    def test_dpt_subclasses_no_duplicate_dpt_number(self):
        """Test for duplicate value_type values in subclasses of DPTTranscoder."""
        dpt_tuples = []
        for dpt in DPTTranscoder.__recursive_subclasses__():
            if hasattr(dpt, 'dpt_main_number') and hasattr(dpt, 'dpt_sub_number'):
                dpt_tuples.append((dpt.dpt_main_number, dpt.dpt_sub_number))
        self.assertCountEqual(dpt_tuples,
                              set(dpt_tuples))

    def test_dpt_alternative_notations(self):
        """Test the parser for accepting alternateive notations for the same DPT class."""
        dpt1 = DPTTranscoder.parse_type("2byte_unsigned")
        dpt2 = DPTTranscoder.parse_type(7)
        dpt3 = DPTTranscoder.parse_type("DPT-7")
        self.assertEqual(dpt1, dpt2)
        self.assertEqual(dpt2, dpt3)

        dpt4 = DPTTranscoder.parse_type("temperature")
        dpt5 = DPTTranscoder.parse_type(9.001)
        dpt6 = DPTTranscoder.parse_type("9.001")
        self.assertEqual(dpt4, dpt5)
        self.assertEqual(dpt5, dpt6)

    def test_dpt_not_implemented(self):
        """Test the parser for processing wrong dpt values."""
        self.assertIsNone(DPTTranscoder.parse_type("unknown"))
        self.assertIsNone(DPTTranscoder.parse_type(0))
        self.assertIsNone(DPTTranscoder.parse_type(5.99999))
        self.assertIsNone(DPTTranscoder.parse_type(["list"]))
