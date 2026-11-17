"""Unit test for KNX DPT 25 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_25 import DoubleNibble, DPTDoubleNibble
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDoubleNibble:
    """Test DoubleNibble class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            ({"busy": 0, "nak": 0}, DoubleNibble(busy=0, nak=0)),
            ({"busy": 3, "nak": 1}, DoubleNibble(busy=3, nak=1)),
            ({"busy": 2, "nak": 3}, DoubleNibble(busy=2, nak=3)),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: DoubleNibble) -> None:
        """Test from_dict and as_dict methods."""
        assert DoubleNibble.from_dict(data) == value
        assert value.as_dict() == data

    @pytest.mark.parametrize(
        "data",
        [
            {"busy": 1},
            {"nak": 1},
            {"busy": "a", "nak": 1},
            {"busy": 1, "nak": None},
            "busy",
        ],
    )
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            DoubleNibble.from_dict(data)


class TestDPTDoubleNibble:
    """Test class for KNX DPTDoubleNibble objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (DoubleNibble(busy=0, nak=0), 0x00),
            (DoubleNibble(busy=0, nak=3), 0x03),
            (DoubleNibble(busy=3, nak=0), 0x30),
            (DoubleNibble(busy=3, nak=3), 0x33),
            (DoubleNibble(busy=1, nak=2), 0x12),
            (DoubleNibble(busy=2, nak=1), 0x21),
        ],
    )
    def test_values(self, value: DoubleNibble, raw: int) -> None:
        """Test DPTDoubleNibble parsing and streaming (busy is the high nibble)."""
        assert DPTDoubleNibble.to_knx(value) == DPTArray(raw)
        assert DPTDoubleNibble.from_knx(DPTArray(raw)) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            ({"busy": 3, "nak": 1}, 0x31),
            ({"busy": "2", "nak": "0"}, 0x20),
        ],
    )
    def test_to_knx_from_dict(self, value: dict[str, Any], raw: int) -> None:
        """Test DPTDoubleNibble serializing from a dict."""
        assert DPTDoubleNibble.to_knx(value) == DPTArray(raw)

    @pytest.mark.parametrize(
        "value",
        [
            DoubleNibble(busy=4, nak=0),
            DoubleNibble(busy=0, nak=4),
            DoubleNibble(busy=-1, nak=0),
            DoubleNibble(busy=0, nak=-1),
            DoubleNibble(busy=15, nak=15),
            DoubleNibble(busy="a", nak=0),  # type: ignore[arg-type]
            DoubleNibble(busy=0, nak=1.5),  # type: ignore[arg-type]
            {"busy": 4, "nak": 0},
            {"busy": 0},
            None,
            0x33,
        ],
    )
    def test_to_knx_wrong_value(self, value: Any) -> None:
        """Test serializing DPTDoubleNibble with a wrong value."""
        with pytest.raises(ConversionError):
            DPTDoubleNibble.to_knx(value)

    @pytest.mark.parametrize("raw", [0x04, 0x40, 0x0F, 0xF0, 0xFF, 0x34])
    def test_from_knx_out_of_range(self, raw: int) -> None:
        """Test parsing DPTDoubleNibble with nibbles out of range 0..3."""
        with pytest.raises(ConversionError):
            DPTDoubleNibble.from_knx(DPTArray(raw))

    @pytest.mark.parametrize(
        "payload",
        [DPTArray(()), DPTArray((0x00, 0x00)), DPTBinary(1)],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing DPTDoubleNibble with a wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTDoubleNibble.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema of DPTDoubleNibble."""
        assert DPTDoubleNibble.get_dict_schema() == [
            {
                "name": "busy",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 3,
            },
            {
                "name": "nak",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 3,
            },
        ]

    def test_lookup(self) -> None:
        """Test lookup of DPTDoubleNibble."""
        assert DPTBase.parse_transcoder("25.1000") is DPTDoubleNibble
        assert DPTBase.parse_transcoder("double_nibble") is DPTDoubleNibble
