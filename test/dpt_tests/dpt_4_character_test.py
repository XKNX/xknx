"""Unit test for KNX character (DPT 4) object."""

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTCharacter, DPTCharacterLatin1
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTCharacter:
    """Test class for KNX single character object."""

    @pytest.mark.parametrize(
        ("string", "raw"),
        [
            ("A", (65,)),
            ("z", (122,)),
            ("0", (48,)),
            ("?", (63,)),
            (" ", (32,)),
            ("", (0,)),  # empty -> NUL byte, stripped on decode
        ],
    )
    @pytest.mark.parametrize("test_dpt", [DPTCharacter, DPTCharacterLatin1])
    def test_values(
        self, string: str, raw: tuple[int, ...], test_dpt: type[DPTCharacter]
    ) -> None:
        """Test parsing and streaming ASCII-range characters for both subtypes."""
        assert test_dpt.to_knx(string) == DPTArray(raw)
        assert test_dpt.from_knx(DPTArray(raw)) == string

    @pytest.mark.parametrize(
        ("string", "knx_string", "raw"),
        [
            ("é", "?", (63,)),
            ("ß", "?", (63,)),
        ],
    )
    def test_to_knx_ascii_invalid_char(
        self, string: str, knx_string: str, raw: tuple[int, ...]
    ) -> None:
        """Test streaming a non-ASCII character replaces it with a question mark."""
        assert DPTCharacter.to_knx(string) == DPTArray(raw)
        assert DPTCharacter.from_knx(DPTArray(raw)) == knx_string

    @pytest.mark.parametrize(
        ("string", "raw"),
        [
            ("é", (0xE9,)),
            ("ÿ", (0xFF,)),
            ("ä", (0xE4,)),
        ],
    )
    def test_to_knx_latin_1(self, string: str, raw: tuple[int, ...]) -> None:
        """Test streaming Latin-1 characters."""
        assert DPTCharacterLatin1.to_knx(string) == DPTArray(raw)
        assert DPTCharacterLatin1.from_knx(DPTArray(raw)) == string

    def test_to_knx_too_long(self) -> None:
        """Test serializing more than one character raises."""
        with pytest.raises(ConversionError):
            DPTCharacter.to_knx("AB")

    @pytest.mark.parametrize(
        "raw",
        [
            (65, 66),  # two octets
            (),  # zero octets
        ],
    )
    def test_from_knx_wrong_parameter_length(self, raw: tuple[int, ...]) -> None:
        """Test parsing with wrong payload length raises."""
        with pytest.raises(CouldNotParseTelegram):
            DPTCharacter.from_knx(DPTArray(raw))

    def test_no_unit_of_measurement(self) -> None:
        """Test that DPT 4 has no unit."""
        assert DPTCharacter.unit is None
        assert DPTCharacterLatin1.unit is None

    def test_transcoder_lookup(self) -> None:
        """Test lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder("4.001") is DPTCharacter
        assert DPTBase.parse_transcoder("4.002") is DPTCharacterLatin1
        assert DPTBase.parse_transcoder("character") is DPTCharacter
        assert DPTBase.parse_transcoder("character_latin_1") is DPTCharacterLatin1
