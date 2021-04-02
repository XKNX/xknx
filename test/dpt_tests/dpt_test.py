"""Unit test for KNX binary/integer objects."""
import pytest
from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.exceptions import ConversionError


class TestDPT:
    """Test class for KNX binary/integer objects."""

    def test_compare_binary(self):
        """Test comparison of DPTBinary objects."""
        assert DPTBinary(0) == DPTBinary(0)
        assert DPTBinary(0) == DPTBinary(False)
        assert DPTBinary(1) == DPTBinary(True)
        assert DPTBinary(2) == DPTBinary(2)
        assert DPTBinary(1) != DPTBinary(4)
        assert DPTBinary(2) != DPTBinary(0)
        assert DPTBinary(0) != DPTBinary(2)

    def test_compare_array(self):
        """Test comparison of DPTArray objects."""
        assert DPTArray(()) == DPTArray(())
        assert DPTArray([1]) == DPTArray((1,))
        assert DPTArray([1, 2, 3]) == DPTArray([1, 2, 3])
        assert DPTArray([1, 2, 3]) == DPTArray((1, 2, 3))
        assert DPTArray((1, 2, 3)) == DPTArray([1, 2, 3])
        assert DPTArray((1, 2, 3)) != DPTArray([1, 2, 3, 4])
        assert DPTArray((1, 2, 3, 4)) != DPTArray([1, 2, 3])
        assert DPTArray((1, 2, 3)) != DPTArray([1, 2, 4])

    def test_compare_none(self):
        """Test comparison DPTArray objects with None."""
        assert DPTArray(()) is not None
        assert None is not DPTArray(())
        assert DPTBinary(0) is not None
        assert None is not DPTBinary(0)
        assert DPTArray((1, 2, 3)) is not None
        assert None is not DPTArray((1, 2, 3))
        assert DPTBinary(1) is not None
        assert None is not DPTBinary(1)

    def test_compare_array_binary(self):
        """Test comparison of empty DPTArray objects with DPTBinary objects."""
        assert DPTArray(()) != DPTBinary(0)
        assert DPTBinary(0) != DPTArray(())
        assert DPTBinary(0) != DPTArray(0)
        assert DPTBinary(1) != DPTArray(1)
        assert DPTArray((1, 2, 3)) != DPTBinary(2)
        assert DPTBinary(2) != DPTArray((1, 2, 3))
        assert DPTArray((2,)) != DPTBinary(2)
        assert DPTBinary(2) != DPTArray((2,))

    def test_dpt_binary_assign(self):
        """Test initialization of DPTBinary objects."""
        assert DPTBinary(8).value == 8

    def test_dpt_binary_assign_limit_exceeded(self):
        """Test initialization of DPTBinary objects with wrong value (value exceeded)."""
        with pytest.raises(ConversionError):
            DPTBinary(DPTBinary.APCI_MAX_VALUE + 1)

    def test_dpt_init_with_string(self):
        """Teest initialization of DPTBinary object with wrong value (wrong type)."""
        with pytest.raises(TypeError):
            DPTBinary("bla")

    def test_dpt_array_init_with_string(self):
        """Test initialization of DPTArray object with wrong value (wrong type)."""
        with pytest.raises(TypeError):
            DPTArray("bla")


class TestDPTBase:
    """Test class for transcoder base object."""

    def test_dpt_subclasses_definition_types(self):
        """Test value_type and dpt_*_number values for correct type in subclasses of DPTBase."""
        for dpt in DPTBase.__recursive_subclasses__():
            if dpt.value_type is not None:
                assert isinstance(
                    dpt.value_type, str
                ), "Wrong type for value_type in {} : {} - str `None` expected".format(
                    dpt,
                    type(dpt.value_type),
                )
            if dpt.dpt_main_number is not None:
                assert isinstance(dpt.dpt_main_number, int), (
                    "Wrong type for dpt_main_number in %s : %s - int or `None` expected"
                    % (dpt, type(dpt.dpt_main_number))
                )
            if dpt.dpt_sub_number is not None:
                assert isinstance(dpt.dpt_sub_number, int), (
                    "Wrong type for dpt_sub_number in %s : %s - int or `None` expected"
                    % (dpt, type(dpt.dpt_sub_number))
                )

    def test_dpt_subclasses_no_duplicate_value_types(self):
        """Test for duplicate value_type values in subclasses of DPTBase."""
        value_types = []
        for dpt in DPTBase.__recursive_subclasses__():
            if dpt.value_type is not None:
                value_types.append(dpt.value_type)
        assert len(value_types) == len(set(value_types))

    def test_dpt_subclasses_no_duplicate_dpt_number(self):
        """Test for duplicate value_type values in subclasses of DPTBase."""
        dpt_tuples = []
        for dpt in DPTBase.__recursive_subclasses__():
            if dpt.dpt_main_number is not None and dpt.dpt_sub_number is not None:
                dpt_tuples.append((dpt.dpt_main_number, dpt.dpt_sub_number))
        assert len(dpt_tuples) == len(set(dpt_tuples))

    def test_dpt_alternative_notations(self):
        """Test the parser for accepting alternateive notations for the same DPT class."""
        dpt1 = DPTBase.parse_transcoder("2byte_unsigned")
        dpt2 = DPTBase.parse_transcoder(7)
        dpt3 = DPTBase.parse_transcoder("DPT-7")
        assert dpt1 == dpt2
        assert dpt2 == dpt3
        dpt4 = DPTBase.parse_transcoder("temperature")
        dpt5 = DPTBase.parse_transcoder("9.001")
        assert dpt4 == dpt5
        dpt7 = DPTBase.parse_transcoder("active_energy")
        dpt8 = DPTBase.parse_transcoder("13.010")
        assert dpt7 == dpt8
