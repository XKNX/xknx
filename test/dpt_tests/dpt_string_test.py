"""Unit test for KNX string object."""
import pytest

from xknx.dpt import DPTArray, DPTLatin1, DPTString
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTString:
    """Test class for KNX ASCII string object."""

    @pytest.mark.parametrize(
        "string,raw",
        [
            (
                "KNX is OK",
                (75, 78, 88, 32, 105, 115, 32, 79, 75, 0, 0, 0, 0, 0),
            ),
            (
                "",
                (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
            ),
            (
                "AbCdEfGhIjKlMn",
                (65, 98, 67, 100, 69, 102, 71, 104, 73, 106, 75, 108, 77, 110),
            ),
            (
                ".,:;-_!?$@&#%/",
                (46, 44, 58, 59, 45, 95, 33, 63, 36, 64, 38, 35, 37, 47),
            ),
        ],
    )
    @pytest.mark.parametrize("test_dpt", [DPTString, DPTLatin1])
    def test_values(self, string, raw, test_dpt):
        """Test parsing and streaming strings."""
        assert test_dpt.to_knx(string) == DPTArray(raw)
        assert test_dpt.from_knx(DPTArray(raw)) == string

    @pytest.mark.parametrize(
        "string,knx_string,raw",
        [
            (
                "Matouš",
                "Matou?",
                (77, 97, 116, 111, 117, 63, 0, 0, 0, 0, 0, 0, 0, 0),
            ),
            (
                "Gänsefüßchen",
                "G?nsef??chen",
                (71, 63, 110, 115, 101, 102, 63, 63, 99, 104, 101, 110, 0, 0),
            ),
        ],
    )
    def test_to_knx_ascii_invalid_chars(self, string, knx_string, raw):
        """Test streaming ASCII string with invalid chars."""
        assert DPTString.to_knx(string) == DPTArray(raw)
        assert DPTString.from_knx(DPTArray(raw)) == knx_string

    @pytest.mark.parametrize(
        "string,raw",
        [
            (
                "Gänsefüßchen",
                (71, 228, 110, 115, 101, 102, 252, 223, 99, 104, 101, 110, 0, 0),
            ),
            (
                "àáâãåæçèéêëìíî",
                (224, 225, 226, 227, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238),
            ),
        ],
    )
    def test_to_knx_latin_1(self, string, raw):
        """Test streaming Latin-1 strings."""
        assert DPTLatin1.to_knx(string) == DPTArray(raw)
        assert DPTLatin1.from_knx(DPTArray(raw)) == string

    def test_to_knx_too_long(self):
        """Test serializing DPTString to KNX with wrong value (to long)."""
        with pytest.raises(ConversionError):
            DPTString.to_knx("AAAAABBBBBCCCCx")

    @pytest.mark.parametrize(
        "raw",
        [
            ((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),),
            ((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),),
        ],
    )
    def test_from_knx_wrong_parameter_length(self, raw):
        """Test parsing of KNX string with wrong elements length."""
        with pytest.raises(CouldNotParseTelegram):
            DPTString.from_knx(DPTArray(raw))

    def test_no_unit_of_measurement(self):
        """Test for no unit set for DPT 16."""
        assert DPTString.unit is None
