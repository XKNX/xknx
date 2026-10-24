"""Unit test for KNX variable length strings - DPT 24.001 and 28.001."""

import pytest

from xknx.dpt import DPTUTF8, DPTArray, DPTBase, DPTBinary, DPTVariableLatin1
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTVariableLatin1:
    """Test class for DPT 24.001 DPT_VarString_8859_1."""

    def test_spec_example(self) -> None:
        """KNX v02.02.01 - Datapoint Types 03.07.02 - §3.24 EXAMPLE 15."""
        raw = (0x4B, 0x4E, 0x58, 0x20, 0x69, 0x73, 0x20, 0x4F, 0x4B, 0x00)
        assert DPTVariableLatin1.to_knx("KNX is OK") == DPTArray(raw)
        assert DPTVariableLatin1.from_knx(DPTArray(raw)) == "KNX is OK"

    def test_latin_1(self) -> None:
        """Test characters of ISO 8859-1 beyond ASCII."""
        assert DPTVariableLatin1.to_knx("Grüße") == DPTArray(
            (0x47, 0x72, 0xFC, 0xDF, 0x65, 0x00)
        )
        assert DPTVariableLatin1.from_knx(DPTArray((0xC4, 0x00))) == "Ä"

    def test_unencodable_character_is_replaced(self) -> None:
        """Test a character outside ISO 8859-1 is sent as question mark."""
        assert DPTVariableLatin1.to_knx("€") == DPTArray((0x3F, 0x00))

    def test_empty_string(self) -> None:
        """Test the empty string is a single NULL."""
        assert DPTVariableLatin1.to_knx("") == DPTArray((0x00,))
        assert DPTVariableLatin1.from_knx(DPTArray((0x00,))) == ""

    def test_from_knx_stops_at_null(self) -> None:
        """Test octets after the terminating NULL are ignored."""
        assert DPTVariableLatin1.from_knx(DPTArray((0x41, 0x00, 0x42))) == "A"

    def test_from_knx_without_null(self) -> None:
        """Test a payload without the terminating NULL is read to its end."""
        assert DPTVariableLatin1.from_knx(DPTArray((0x41, 0x42))) == "AB"

    def test_maximum_length(self) -> None:
        """Test the longest string fills the payload of an extended frame."""
        longest = "x" * (DPTVariableLatin1.payload_length - 1)
        payload = DPTVariableLatin1.to_knx(longest)
        assert len(payload.value) == DPTVariableLatin1.payload_length == 253
        assert DPTVariableLatin1.from_knx(payload) == longest
        with pytest.raises(ConversionError):
            DPTVariableLatin1.to_knx(longest + "x")

    def test_to_knx_null_inside(self) -> None:
        """Test a NULL inside the string is rejected."""
        with pytest.raises(ConversionError):
            DPTVariableLatin1.to_knx("A\x00B")

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray(()),
            DPTArray((0x41,) * 254),
            DPTBinary(0),
        ],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test an empty, too long or binary payload is rejected."""
        with pytest.raises(CouldNotParseTelegram):
            DPTVariableLatin1.from_knx(payload)


class TestDPTUTF8:
    """Test class for DPT 28.001 DPT_UTF-8."""

    @pytest.mark.parametrize(
        ("string", "raw"),
        [
            ("KNX", (0x4B, 0x4E, 0x58, 0x00)),
            # one octet up to four octets per character, KNX v02.02.01 - Datapoint Types
            # 03.07.02 - §3.27.1
            ("ü", (0xC3, 0xBC, 0x00)),
            ("€", (0xE2, 0x82, 0xAC, 0x00)),
            ("😀", (0xF0, 0x9F, 0x98, 0x80, 0x00)),
        ],
    )
    def test_values(self, string: str, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming UTF-8 strings."""
        assert DPTUTF8.to_knx(string) == DPTArray(raw)
        assert DPTUTF8.from_knx(DPTArray(raw)) == string

    def test_invalid_utf_8_is_replaced(self) -> None:
        """Test an invalid octet sequence decodes to the replacement character."""
        assert DPTUTF8.from_knx(DPTArray((0xC3, 0x00))) == "�"

    def test_maximum_length_counts_octets(self) -> None:
        """Test the maximum length is in octets, not characters."""
        fits = "€" * ((DPTUTF8.payload_length - 1) // 3)
        assert len(DPTUTF8.to_knx(fits).value) <= DPTUTF8.payload_length
        with pytest.raises(ConversionError):
            DPTUTF8.to_knx(fits + "€")

    def test_lookup(self) -> None:
        """Test both types are found by number and value type."""
        assert DPTBase.parse_transcoder("28.001") is DPTUTF8
        assert DPTBase.parse_transcoder("utf_8") is DPTUTF8
        assert DPTBase.parse_transcoder("24.001") is DPTVariableLatin1
        assert DPTBase.parse_transcoder("variable_latin_1") is DPTVariableLatin1
