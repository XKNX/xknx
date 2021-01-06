"""Unit test for KNX binary/integer objects."""
import unittest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.exceptions import ConversionError


class TestDPT(unittest.TestCase):
    """Test class for KNX binary/integer objects."""

    # pylint: disable=too-many-public-methods,invalid-name

    def test_compare_binary(self):
        """Test comparison of DPTBinary objects."""
        self.assertEqual(DPTBinary(0), DPTBinary(0))
        self.assertEqual(DPTBinary(0), DPTBinary(False))
        self.assertEqual(DPTBinary(1), DPTBinary(True))
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
        """Test comparison DPTArray objects with None."""
        self.assertNotEqual(DPTArray(()), None)
        self.assertNotEqual(None, DPTArray(()))
        self.assertNotEqual(DPTBinary(0), None)
        self.assertNotEqual(None, DPTBinary(0))
        self.assertNotEqual(DPTArray((1, 2, 3)), None)
        self.assertNotEqual(None, DPTArray((1, 2, 3)))
        self.assertNotEqual(DPTBinary(1), None)
        self.assertNotEqual(None, DPTBinary(1))

    def test_compare_array_binary(self):
        """Test comparison of empty DPTArray objects with DPTBinary objects."""
        self.assertNotEqual(DPTArray(()), DPTBinary(0))
        self.assertNotEqual(DPTBinary(0), DPTArray(()))
        self.assertNotEqual(DPTBinary(0), DPTArray(0))
        self.assertNotEqual(DPTBinary(1), DPTArray(1))
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


class TestDPTBase(unittest.TestCase):
    """Test class for transcoder base object."""

    def test_dpt_subclasses_definition_types(self):
        """Test value_type and dpt_*_number values for correct type in subclasses of DPTBase."""
        for dpt in DPTBase.__recursive_subclasses__():
            if hasattr(dpt, "value_type"):
                self.assertTrue(
                    isinstance(dpt.value_type, str),
                    msg="Wrong type for value_type in %s - str expected" % dpt,
                )
            if hasattr(dpt, "dpt_main_number"):
                self.assertTrue(
                    isinstance(dpt.dpt_main_number, int),
                    msg="Wrong type for dpt_main_number in %s - int expected" % dpt,
                )
            if hasattr(dpt, "dpt_sub_number"):
                self.assertTrue(
                    isinstance(dpt.dpt_sub_number, (int, type(None))),
                    msg="Wrong type for dpt_sub_number in %s - int or `None` expected"
                    % dpt,
                )

    def test_dpt_subclasses_no_duplicate_value_types(self):
        """Test for duplicate value_type values in subclasses of DPTBase."""
        value_types = []
        for dpt in DPTBase.__recursive_subclasses__():
            if hasattr(dpt, "value_type"):
                value_types.append(dpt.value_type)
        self.assertCountEqual(value_types, set(value_types))

    def test_dpt_subclasses_have_both_dpt_number_attributes(self):
        """Test DPTBase subclasses for having both dpt number attributes set."""
        for dpt in DPTBase.__recursive_subclasses__():
            if hasattr(dpt, "dpt_main_number"):
                self.assertTrue(
                    hasattr(dpt, "dpt_sub_number"), "No dpt_sub_number in %s" % dpt
                )

    def test_dpt_subclasses_no_duplicate_dpt_number(self):
        """Test for duplicate value_type values in subclasses of DPTBase."""
        dpt_tuples = []
        for dpt in DPTBase.__recursive_subclasses__():
            if hasattr(dpt, "dpt_main_number") and hasattr(dpt, "dpt_sub_number"):
                dpt_tuples.append((dpt.dpt_main_number, dpt.dpt_sub_number))
        self.assertCountEqual(dpt_tuples, set(dpt_tuples))

    def test_dpt_alternative_notations(self):
        """Test the parser for accepting alternateive notations for the same DPT class."""
        dpt1 = DPTBase.parse_transcoder("2byte_unsigned")
        dpt2 = DPTBase.parse_transcoder(7)
        dpt3 = DPTBase.parse_transcoder("DPT-7")
        self.assertEqual(dpt1, dpt2)
        self.assertEqual(dpt2, dpt3)
        dpt4 = DPTBase.parse_transcoder("temperature")
        dpt5 = DPTBase.parse_transcoder(9.001)
        dpt6 = DPTBase.parse_transcoder("9.001")
        self.assertEqual(dpt4, dpt5)
        self.assertEqual(dpt5, dpt6)
        dpt7 = DPTBase.parse_transcoder("active_energy")
        dpt8 = DPTBase.parse_transcoder(13.010)
        self.assertEqual(dpt7, dpt8, "parsing float failed")
