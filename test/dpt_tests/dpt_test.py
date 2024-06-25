"""Unit test for KNX binary/integer objects."""

from typing import Any

import pytest

from xknx.dpt import (
    DPT2ByteFloat,
    DPTArray,
    DPTBase,
    DPTBinary,
    DPTColorRGBW,
    DPTComplex,
    DPTEnum,
    DPTHVACContrMode,
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
            assert dpt not in (DPTBase, DPTNumeric, DPTEnum, DPTComplex)

    def test_dpt_concrete_subclasses_included(self):
        """Test if concrete subclasses are included by dpt_class_tree."""
        for dpt in (
            DPT2ByteFloat,
            DPTString,
            DPTTemperature,
            DPTScaling,
            DPTHVACContrMode,
            DPTColorRGBW,
        ):
            assert dpt in DPTBase.dpt_class_tree()

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

    @pytest.mark.parametrize(
        "equal_dpts",
        [
            # strings in dictionaries would fail type checking, but should work nevertheless
            ["2byte_unsigned", 7, "DPT-7", {"main": 7}, {"main": "7", "sub": None}],
            ["temperature", "9.001", {"main": 9, "sub": 1}, {"main": "9", "sub": "1"}],
            ["active_energy", "13.010", {"main": 13, "sub": 10}],
        ],
    )
    def test_dpt_alternative_notations(self, equal_dpts: list[Any]):
        """Test the parser for accepting alternative notations for the same DPT class."""
        parsed = [DPTBase.parse_transcoder(dpt) for dpt in equal_dpts]
        assert issubclass(parsed[0], DPTBase)
        assert all(parsed[0] == dpt for dpt in parsed)

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

    @pytest.mark.parametrize(
        "value",
        [
            None,
            0,
            999999999,
            9.001,  # float is not valid
            "invalid_string",
            {"sub": 1},
            {"main": None, "sub": None},
            {"main": "invalid"},
            {"main": 9, "sub": "invalid"},
            [9, 1],
            (9,),
        ],
    )
    def test_parse_transcoder_invalid_data(self, value: Any):
        """Test parsing invalid data."""
        assert DPTBase.parse_transcoder(value) is None


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

        assert isinstance(dpt_class.value_min, int | float)
        assert isinstance(dpt_class.value_max, int | float)
        assert isinstance(dpt_class.resolution, int | float)
