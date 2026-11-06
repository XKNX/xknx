"""Unit test for KNX DPT 20.011 system error classes."""

import pytest

from xknx.dpt import DPTArray, DPTErrorClassSystem
from xknx.dpt.dpt_20 import ErrorClassSystem
from xknx.exceptions import ConversionError


class TestDPTErrorClassSystem:
    """Test class for KNX DPT 20.011 system error classes."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (ErrorClassSystem.NO_FAULT, 0x00),
            (ErrorClassSystem.CRC_ERROR, 0x09),
            (ErrorClassSystem.GROUP_OBJECT_TYPE_EXCEEDS_MAX_APDU_LENGTH, 0x12),
        ],
    )
    def test_to_and_from_knx(self, value: ErrorClassSystem, raw: int) -> None:
        """Test parsing and streaming DPTErrorClassSystem."""
        assert DPTErrorClassSystem.to_knx(value) == DPTArray((raw,))
        assert DPTErrorClassSystem.from_knx(DPTArray((raw,))) == value

    def test_to_knx_by_string(self) -> None:
        """Test parsing DPTErrorClassSystem string values to KNX."""
        assert DPTErrorClassSystem.to_knx("crc_error") == DPTArray((0x09,))

    def test_reserved_values(self) -> None:
        """Test that reserved values are rejected."""
        with pytest.raises(ConversionError):
            DPTErrorClassSystem.to_knx(19)
        with pytest.raises(ConversionError):
            DPTErrorClassSystem.from_knx(DPTArray((0x13,)))

    def test_lookup(self) -> None:
        """Test looking up DPTErrorClassSystem by number and value type."""
        assert DPTErrorClassSystem.parse_transcoder("error_class_system") is (
            DPTErrorClassSystem
        )
        assert DPTErrorClassSystem.parse_transcoder("20.011") is DPTErrorClassSystem
