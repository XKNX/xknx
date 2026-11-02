"""Unit test for KNX DPT 240 objects."""

from typing import Any

import pytest

from xknx.dpt import (
    CombinedPosition,
    DPTArray,
    DPTBase,
    DPTBinary,
    DPTCombinedPosition,
    DPTComplex,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestCombinedPosition:
    """Test CombinedPosition class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {"height_position": 0, "slats_position": 100},
                CombinedPosition(0, 100),
            ),
            ({"height_position": 50}, CombinedPosition(50, None)),
            ({"slats_position": 25}, CombinedPosition(None, 25)),
            (
                {"height_position": None, "slats_position": 75},
                CombinedPosition(None, 75),
            ),
            ({"height_position": "30", "slats_position": 40}, CombinedPosition(30, 40)),
            # an empty dict is a valid telegram with both positions invalid
            ({}, CombinedPosition()),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: CombinedPosition) -> None:
        """Test from_dict and as_dict methods."""
        assert CombinedPosition.from_dict(data) == value
        default_dict = {"height_position": None, "slats_position": None}
        assert value.as_dict() == default_dict | {
            key: int(val) for key, val in data.items() if val is not None
        }

    @pytest.mark.parametrize(
        "data",
        [
            {"height_position": "a", "slats_position": 0},
            {"height_position": 0, "slats_position": "a"},
            {"height_position": [1]},
            1,
            None,
            "height_position",
            [("height_position", 1)],
        ],
    )
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid values."""
        with pytest.raises(ValueError):
            CombinedPosition.from_dict(data)


class TestDPTCombinedPosition:
    """Test class for KNX DPTCombinedPosition objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (CombinedPosition(0, 0), (0x00, 0x00, 0x03)),
            (CombinedPosition(100, 100), (0xFF, 0xFF, 0x03)),
            (CombinedPosition(50, 25), (0x80, 0x40, 0x03)),
            (CombinedPosition(1, 99), (0x03, 0xFC, 0x03)),
            (CombinedPosition(75, None), (0xBF, 0x00, 0x01)),
            (CombinedPosition(None, 75), (0x00, 0xBF, 0x02)),
            (CombinedPosition(None, None), (0x00, 0x00, 0x00)),
        ],
    )
    def test_round_trip(self, value: CombinedPosition, raw: tuple[int, ...]) -> None:
        """Test DPTCombinedPosition parsing and streaming."""
        knx_value = DPTCombinedPosition.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTCombinedPosition.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        ("raw", "value"),
        [
            # positions of invalid fields are ignored
            ((0x80, 0xFF, 0x01), CombinedPosition(50, None)),
            ((0xFF, 0x80, 0x02), CombinedPosition(None, 50)),
            ((0xFF, 0xFF, 0x00), CombinedPosition(None, None)),
            # reserved bits are ignored
            ((0x80, 0x80, 0xFF), CombinedPosition(50, 50)),
            ((0x80, 0x80, 0xFC), CombinedPosition(None, None)),
            # values are rounded to full percent
            ((0x01, 0xFE, 0x03), CombinedPosition(0, 100)),
        ],
    )
    def test_from_knx(self, raw: tuple[int, ...], value: CombinedPosition) -> None:
        """Test DPTCombinedPosition parsing of raw values."""
        assert DPTCombinedPosition.from_knx(DPTArray(raw)) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            ({"height_position": 50, "slats_position": 25}, (0x80, 0x40, 0x03)),
            ({"slats_position": 100}, (0x00, 0xFF, 0x02)),
            ({}, (0x00, 0x00, 0x00)),
        ],
    )
    def test_to_knx_from_dict(
        self, value: dict[str, Any], raw: tuple[int, ...]
    ) -> None:
        """Test DPTCombinedPosition serializing from a dict."""
        assert DPTCombinedPosition.to_knx(value) == DPTArray(raw)

    @pytest.mark.parametrize(
        "value",
        [
            CombinedPosition(-1, 0),
            CombinedPosition(101, 0),
            CombinedPosition(0, -1),
            CombinedPosition(0, 101),
            CombinedPosition("a", 0),  # type: ignore[arg-type]
            CombinedPosition(0, "a"),  # type: ignore[arg-type]
            {"height_position": 101},
            {"slats_position": "a"},
            None,
            1,
            (0x00, 0x00, 0x03),
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test DPTCombinedPosition serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTCombinedPosition.to_knx(value)

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x80, 0x80)),
            DPTArray((0x80, 0x80, 0x03, 0x00)),
            DPTBinary(1),
        ],
    )
    def test_from_knx_invalid_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test DPTCombinedPosition parsing invalid payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTCombinedPosition.from_knx(payload)

    @pytest.mark.parametrize("value_type", ["240.800", "combined_position"])
    def test_lookup(self, value_type: str) -> None:
        """Test transcoder lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder(value_type) is DPTCombinedPosition
        assert DPTComplex.parse_transcoder(value_type) is DPTCombinedPosition
        assert (
            DPTBase.parse_transcoder({"main": 240, "sub": 800}) is DPTCombinedPosition
        )

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTCombinedPosition."""
        assert DPTCombinedPosition.get_dict_schema() == [
            {
                "name": "height_position",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 100,
            },
            {
                "name": "slats_position",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 100,
            },
        ]
