"""Unit test for KNX DPT 255 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_255 import DPTGeographicalLocation, GeographicalLocation
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestGeographicalLocation:
    """Test GeographicalLocation class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {"longitude": 11.5, "latitude": 48.25},
                GeographicalLocation(11.5, 48.25),
            ),
            (
                {"longitude": -180, "latitude": "-90"},
                GeographicalLocation(-180.0, -90.0),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: GeographicalLocation) -> None:
        """Test from_dict and as_dict methods."""
        assert GeographicalLocation.from_dict(data) == value
        assert value.as_dict() == {
            "longitude": float(data["longitude"]),
            "latitude": float(data["latitude"]),
        }

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"longitude": 11.5},
            {"latitude": 48.25},
            {"longitude": None, "latitude": 48.25},
            {"longitude": "a", "latitude": 48.25},
            {"longitude": 11.5, "latitude": "a"},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            GeographicalLocation.from_dict(data)


class TestDPTGeographicalLocation:
    """Test class for KNX DPTGeographicalLocation objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                GeographicalLocation(0.0, 0.0),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                GeographicalLocation(180.0, 90.0),
                (0x43, 0x34, 0x00, 0x00, 0x42, 0xB4, 0x00, 0x00),
            ),
            (
                GeographicalLocation(-180.0, -90.0),
                (0xC3, 0x34, 0x00, 0x00, 0xC2, 0xB4, 0x00, 0x00),
            ),
            (
                GeographicalLocation(1.5, -45.25),
                (0x3F, 0xC0, 0x00, 0x00, 0xC2, 0x35, 0x00, 0x00),
            ),
            (
                GeographicalLocation(11.5755, 48.1374),
                (0x41, 0x39, 0x35, 0x3F, 0x42, 0x40, 0x8C, 0xB3),
            ),
        ],
    )
    def test_value(self, value: GeographicalLocation, raw: tuple[int, ...]) -> None:
        """Test parsing and streaming."""
        knx_value = DPTGeographicalLocation.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTGeographicalLocation.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test serializing a dict."""
        assert DPTGeographicalLocation.to_knx(
            {"longitude": 1.5, "latitude": -45.25}
        ) == DPTArray((0x3F, 0xC0, 0x00, 0x00, 0xC2, 0x35, 0x00, 0x00))

    @pytest.mark.parametrize(
        "value",
        [
            GeographicalLocation(180.1, 0.0),
            GeographicalLocation(-180.1, 0.0),
            GeographicalLocation(0.0, 90.1),
            GeographicalLocation(0.0, -90.1),
            GeographicalLocation(float("nan"), 0.0),
            GeographicalLocation(0.0, float("inf")),
            GeographicalLocation("a", 0.0),  # type: ignore[arg-type]
            {"longitude": 181, "latitude": 0},
            {"longitude": 0},
            None,
            1,
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTGeographicalLocation.to_knx(value)

    @pytest.mark.parametrize(
        "raw",
        [
            (0x43, 0x34, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00),  # 180.5 longitude
            (0x00, 0x00, 0x00, 0x00, 0x42, 0xB5, 0x00, 0x00),  # 90.5 latitude
            (0x7F, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),  # NaN longitude
            (0x00, 0x00, 0x00, 0x00, 0xFF, 0x80, 0x00, 0x00),  # -inf latitude
        ],
    )
    def test_from_knx_out_of_range(self, raw: tuple[int, ...]) -> None:
        """Test parsing out of range coordinates."""
        with pytest.raises(ConversionError):
            DPTGeographicalLocation.from_knx(DPTArray(raw))

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00,) * 7),
            DPTArray((0x00,) * 9),
            DPTBinary(0),
        ],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing wrong payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTGeographicalLocation.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema."""
        assert DPTGeographicalLocation.get_dict_schema() == [
            {
                "name": "longitude",
                "type": "float",
                "required": True,
                "value_min": -180.0,
                "value_max": 180.0,
            },
            {
                "name": "latitude",
                "type": "float",
                "required": True,
                "value_min": -90.0,
                "value_max": 90.0,
            },
        ]

    @pytest.mark.parametrize("value_type", ["255.001", "geographical_location"])
    def test_parse_transcoder(self, value_type: str) -> None:
        """Test lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder(value_type) is DPTGeographicalLocation
