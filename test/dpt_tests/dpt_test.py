"""Unit test for KNX binary/integer objects."""
import pytest

from xknx.dpt import (
    DPT2ByteFloat,
    DPTArray,
    DPTBase,
    DPTBinary,
    DPTNumeric,
    DPTScaling,
    DPTString,
    DPTTemperature,
)
from xknx.exceptions import CouldNotParseTelegram


class TestDPTBase:
    """Test class for transcoder base object."""

    def test_dpt_abstract_subclasses_ignored(self):
        """Test if abstract base classes are ignored by dpt_class_tree and __recursive_subclasses__."""
        for dpt in DPTBase.dpt_class_tree():
            assert dpt not in (DPTBase, DPTNumeric)

    @pytest.mark.parametrize("dpt_class", [DPTString, DPT2ByteFloat])
    def test_dpt_non_abstract_baseclass_included(self, dpt_class):
        """Test if non-abstract base classes is included by dpt_class_tree."""
        assert dpt_class in dpt_class.dpt_class_tree()

    def test_dpt_subclasses_definition_types(self):
        """Test value_type and dpt_*_number values for correct type in subclasses of DPTBase."""
        for dpt in DPTBase.dpt_class_tree():
            if dpt.value_type is not None:
                assert isinstance(
                    dpt.value_type, str
                ), f"Wrong type for value_type in {dpt} : {type(dpt.value_type)} - str `None` expected"
            if dpt.dpt_main_number is not None:
                assert isinstance(
                    dpt.dpt_main_number, int
                ), f"Wrong type for dpt_main_number in {dpt} : {type(dpt.dpt_main_number)} - int or `None` expected"
            if dpt.dpt_sub_number is not None:
                assert isinstance(
                    dpt.dpt_sub_number, int
                ), f"Wrong type for dpt_sub_number in {dpt} : {type(dpt.dpt_sub_number)} - int or `None` expected"

    def test_dpt_subclasses_no_duplicate_value_types(self):
        """Test for duplicate value_type values in subclasses of DPTBase."""
        value_types = [
            dpt.value_type
            for dpt in DPTBase.dpt_class_tree()
            if dpt.value_type is not None
        ]
        assert len(value_types) == len(set(value_types))

    def test_dpt_subclasses_no_duplicate_dpt_number(self):
        """Test for duplicate value_type values in subclasses of DPTBase."""
        dpt_tuples = [
            (dpt.dpt_main_number, dpt.dpt_sub_number)
            for dpt in DPTBase.dpt_class_tree()
            if dpt.dpt_main_number is not None and dpt.dpt_sub_number is not None
        ]
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

    def test_parse_transcoder_from_subclass(self):
        """Test parsing only subclasses of a DPT class."""
        assert DPTBase.parse_transcoder("string") == DPTString
        assert DPTNumeric.parse_transcoder("string") is None
        assert DPT2ByteFloat.parse_transcoder("string") is None

        assert DPTBase.parse_transcoder("percent") == DPTScaling
        assert DPTNumeric.parse_transcoder("percent") == DPTScaling
        assert DPT2ByteFloat.parse_transcoder("percent") is None

        assert DPTBase.parse_transcoder("temperature") == DPTTemperature
        assert DPTNumeric.parse_transcoder("temperature") == DPTTemperature
        assert DPT2ByteFloat.parse_transcoder("temperature") == DPTTemperature


class TestDPTBaseSubclass:
    """Test subclass of transcoder base object."""

    @pytest.mark.parametrize("dpt_class", DPTBase.dpt_class_tree())
    def test_required_values(self, dpt_class):
        """Test required class variables are set for definitions."""
        assert dpt_class.payload_type in (DPTArray, DPTBinary)
        assert dpt_class.payload_length is not None

    def test_validate_payload_array(self):
        """Test validate_payload method."""

        class DPTArrayTest(DPTBase):
            payload_type = DPTArray
            payload_length = 2

        with pytest.raises(CouldNotParseTelegram):
            DPTArrayTest.validate_payload(DPTArray((1,)))
        with pytest.raises(CouldNotParseTelegram):
            DPTArrayTest.validate_payload(DPTArray((1, 1, 1)))
        with pytest.raises(CouldNotParseTelegram):
            DPTArrayTest.validate_payload(DPTBinary(1))
        with pytest.raises(CouldNotParseTelegram):
            DPTArrayTest.validate_payload("why?")

        assert DPTArrayTest.validate_payload(DPTArray((1, 1))) == (1, 1)

    def test_validate_payload_binary(self):
        """Test validate_payload method."""

        class DPTBinaryTest(DPTBase):
            payload_type = DPTBinary
            payload_length = 1

        with pytest.raises(CouldNotParseTelegram):
            DPTBinaryTest.validate_payload(DPTArray(1))
        with pytest.raises(CouldNotParseTelegram):
            DPTBinaryTest.validate_payload(DPTArray((1, 1)))
        with pytest.raises(CouldNotParseTelegram):
            DPTBinaryTest.validate_payload("why?")

        assert DPTBinaryTest.validate_payload(DPTBinary(1)) == (1,)


class TestDPTNumeric:
    """Test class for numeric transcoder base object."""

    @pytest.mark.parametrize("dpt_class", DPTNumeric.dpt_class_tree())
    def test_values(self, dpt_class):
        """Test boundary values are set for numeric definitions (because mypy doesn't)."""

        assert isinstance(dpt_class.value_min, (int, float))
        assert isinstance(dpt_class.value_max, (int, float))
        assert isinstance(dpt_class.resolution, (int, float))
