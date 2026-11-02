"""Unit test for KNX DPT 234 language and region code objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary, DPTString
from xknx.dpt.dpt_234 import DPTLanguageCodeAlpha2ASCII, DPTRegionCodeAlpha2ASCII
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTLanguageCodeAlpha2ASCII:
    """Test class for KNX DPT 234.001 objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            ("de", (0x64, 0x65)),  # spec example
            ("en", (0x65, 0x6E)),  # spec example
            ("aa", (0x61, 0x61)),
            ("zz", (0x7A, 0x7A)),
        ],
    )
    def test_values(self, value: str, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming."""
        assert DPTLanguageCodeAlpha2ASCII.to_knx(value) == DPTArray(raw)
        assert DPTLanguageCodeAlpha2ASCII.from_knx(DPTArray(raw)) == value

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("DE", "de"), ("En", "en"), ("fR", "fr")],
    )
    def test_case_insensitive(self, value: str, expected: str) -> None:
        """Test lower case is sent and upper case is decoded to lower case."""
        raw = DPTLanguageCodeAlpha2ASCII.to_knx(value)
        assert raw == DPTArray(expected.encode("ascii"))
        assert (
            DPTLanguageCodeAlpha2ASCII.from_knx(DPTArray(value.encode("ascii")))
            == expected
        )

    @pytest.mark.parametrize(
        "value",
        ["", "d", "deu", "d1", "1e", "d ", "dé", "ßa", None, 12, ("d", "e")],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTLanguageCodeAlpha2ASCII.to_knx(value)

    @pytest.mark.parametrize(
        "raw",
        [
            (0x00, 0x00),
            (0x64, 0x00),
            (0x31, 0x32),
            (0x64, 0x20),
            (0xE9, 0x65),
            (0xFF, 0xFF),
        ],
    )
    def test_from_knx_invalid(self, raw: tuple[int, ...]) -> None:
        """Test parsing payloads that are no two ASCII letters."""
        with pytest.raises(ConversionError):
            DPTLanguageCodeAlpha2ASCII.from_knx(DPTArray(raw))

    @pytest.mark.parametrize(
        "payload",
        [DPTArray(()), DPTArray((0x64,)), DPTArray((0x64, 0x65, 0x00)), DPTBinary(1)],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing wrong payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTLanguageCodeAlpha2ASCII.from_knx(payload)

    def test_transcoder_lookup(self) -> None:
        """Test lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder("234.001") is DPTLanguageCodeAlpha2ASCII
        assert (
            DPTBase.parse_transcoder("language_code_alpha2")
            is DPTLanguageCodeAlpha2ASCII
        )
        assert DPTString.parse_transcoder("234.001") is DPTLanguageCodeAlpha2ASCII
        assert DPTLanguageCodeAlpha2ASCII.unit is None


class TestDPTRegionCodeAlpha2ASCII:
    """Test class for KNX DPT 234.002 objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            ("DE", (0x44, 0x45)),  # spec example
            ("GB", (0x47, 0x42)),  # spec example
            ("AA", (0x41, 0x41)),
            ("ZZ", (0x5A, 0x5A)),
        ],
    )
    def test_values(self, value: str, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming."""
        assert DPTRegionCodeAlpha2ASCII.to_knx(value) == DPTArray(raw)
        assert DPTRegionCodeAlpha2ASCII.from_knx(DPTArray(raw)) == value

    @pytest.mark.parametrize(
        ("value", "expected"),
        [("de", "DE"), ("Gb", "GB"), ("uS", "US")],
    )
    def test_case_insensitive(self, value: str, expected: str) -> None:
        """Test upper case is sent and lower case is decoded to upper case."""
        raw = DPTRegionCodeAlpha2ASCII.to_knx(value)
        assert raw == DPTArray(expected.encode("ascii"))
        assert (
            DPTRegionCodeAlpha2ASCII.from_knx(DPTArray(value.encode("ascii")))
            == expected
        )

    @pytest.mark.parametrize("value", ["", "D", "DEU", "D1", "Ä1", None, 1])
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTRegionCodeAlpha2ASCII.to_knx(value)

    @pytest.mark.parametrize("raw", [(0x00, 0x00), (0x44, 0x00), (0xC4, 0x45)])
    def test_from_knx_invalid(self, raw: tuple[int, ...]) -> None:
        """Test parsing payloads that are no two ASCII letters."""
        with pytest.raises(ConversionError):
            DPTRegionCodeAlpha2ASCII.from_knx(DPTArray(raw))

    def test_from_knx_wrong_payload(self) -> None:
        """Test parsing wrong payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTRegionCodeAlpha2ASCII.from_knx(DPTArray((0x44, 0x45, 0x00)))

    def test_transcoder_lookup(self) -> None:
        """Test lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder("234.002") is DPTRegionCodeAlpha2ASCII
        assert (
            DPTBase.parse_transcoder("region_code_alpha2") is DPTRegionCodeAlpha2ASCII
        )
        assert DPTRegionCodeAlpha2ASCII.unit is None
