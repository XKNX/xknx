"""Unit test for KNX DPT 275 objects."""

from typing import Any

import pytest

from xknx.dpt import (
    DPTArray,
    DPTRoomTemperatureSetpointSet,
    DPTRoomTemperatureSetpointSetShift,
    RoomTemperatureSetpoints,
    RoomTemperatureSetpointsShift,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestRoomTemperatureSetpoints:
    """Test RoomTemperatureSetpoints class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {
                    "comfort": 21.0,
                    "standby": 19.0,
                    "economy": 16.0,
                    "building_protection": 5.0,
                },
                RoomTemperatureSetpoints(21.0, 19.0, 16.0, 5.0),
            ),
            (
                {"comfort": 2, "standby": 0, "economy": -2, "building_protection": -5},
                RoomTemperatureSetpoints(2.0, 0.0, -2.0, -5.0),
            ),
            ({"comfort": 21.0}, RoomTemperatureSetpoints(comfort=21.0)),
            ({}, RoomTemperatureSetpoints()),
            (
                {"comfort": None, "standby": 19.0},
                RoomTemperatureSetpoints(standby=19.0),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: RoomTemperatureSetpoints) -> None:
        """Test from_dict and as_dict methods."""
        test_value = RoomTemperatureSetpoints.from_dict(data)
        assert test_value == value
        # fields default to `None`
        default_dict = {
            "comfort": None,
            "standby": None,
            "economy": None,
            "building_protection": None,
        }
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            {"comfort": "a"},
            {"standby": "a"},
            {"economy": "a"},
            {"building_protection": "a"},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            RoomTemperatureSetpoints.from_dict(data)


class TestDPTRoomTemperatureSetpointSet:
    """Test class for KNX DPTRoomTemperatureSetpointSet objects (DPT 275.100)."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                RoomTemperatureSetpoints(21.0, 19.0, 16.0, 5.0),
                (0x0C, 0x1A, 0x07, 0x6C, 0x06, 0x40, 0x01, 0xF4),
            ),
            (
                RoomTemperatureSetpoints(0.0, 0.0, 0.0, 0.0),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                # all fields "not used"
                RoomTemperatureSetpoints(),
                (0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
            (
                # only comfort set, rest "not used"
                RoomTemperatureSetpoints(comfort=21.0),
                (0x0C, 0x1A, 0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
        ],
    )
    def test_value(self, value: RoomTemperatureSetpoints, raw: tuple[int, ...]) -> None:
        """Test DPTRoomTemperatureSetpointSet parsing and streaming."""
        knx_value = DPTRoomTemperatureSetpointSet.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTRoomTemperatureSetpointSet.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test DPTRoomTemperatureSetpointSet parsing from a dict."""
        value = {
            "comfort": 21.0,
            "standby": 19.0,
            "economy": 16.0,
            "building_protection": 5.0,
        }
        knx_value = DPTRoomTemperatureSetpointSet.to_knx(value)
        assert knx_value == DPTArray((0x0C, 0x1A, 0x07, 0x6C, 0x06, 0x40, 0x01, 0xF4))

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            (0xFF, 0x4E),
            RoomTemperatureSetpoints(21.0, 19.0, 16.0, "a"),
            # below absolute zero - out of DPTTemperature's range
            RoomTemperatureSetpoints(comfort=-300.0),
            # encodes to the same bits as "not used" (0x7FFF)
            RoomTemperatureSetpoints(comfort=670760.0),
        ],
    )
    def test_wrong_value_to_knx(self, value: Any) -> None:
        """Test DPTRoomTemperatureSetpointSet parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTRoomTemperatureSetpointSet.to_knx(value)

    def test_wrong_value_from_knx(self) -> None:
        """Test DPTRoomTemperatureSetpointSet parsing with wrong payload length."""
        with pytest.raises(CouldNotParseTelegram):
            DPTRoomTemperatureSetpointSet.from_knx(DPTArray((0xFF, 0x4E)))

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema."""
        field_schema = {
            "type": "float",
            "required": False,
            "value_min": -273.0,
            "value_max": 670760.0,
            "resolution": 0.01,
        }
        assert DPTRoomTemperatureSetpointSet.get_dict_schema() == [
            {"name": "comfort", **field_schema},
            {"name": "standby", **field_schema},
            {"name": "economy", **field_schema},
            {"name": "building_protection", **field_schema},
        ]


class TestRoomTemperatureSetpointsShift:
    """Test RoomTemperatureSetpointsShift class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {
                    "comfort": 2.5,
                    "standby": 0.0,
                    "economy": -2.5,
                    "building_protection": -5.0,
                },
                RoomTemperatureSetpointsShift(2.5, 0.0, -2.5, -5.0),
            ),
            ({}, RoomTemperatureSetpointsShift()),
        ],
    )
    def test_dict(
        self, data: dict[str, Any], value: RoomTemperatureSetpointsShift
    ) -> None:
        """Test from_dict and as_dict methods."""
        test_value = RoomTemperatureSetpointsShift.from_dict(data)
        assert test_value == value
        default_dict = {
            "comfort": None,
            "standby": None,
            "economy": None,
            "building_protection": None,
        }
        assert value.as_dict() == default_dict | data

    def test_dict_invalid(self) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            RoomTemperatureSetpointsShift.from_dict({"comfort": "a"})


class TestDPTRoomTemperatureSetpointSetShift:
    """Test class for KNX DPTRoomTemperatureSetpointSetShift objects (DPT 275.101)."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                RoomTemperatureSetpointsShift(2.5, 0.0, -2.5, -5.0),
                (0x00, 0xFA, 0x00, 0x00, 0x87, 0x06, 0x86, 0x0C),
            ),
            (
                RoomTemperatureSetpointsShift(),
                (0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
        ],
    )
    def test_value(
        self, value: RoomTemperatureSetpointsShift, raw: tuple[int, ...]
    ) -> None:
        """Test DPTRoomTemperatureSetpointSetShift parsing and streaming."""
        knx_value = DPTRoomTemperatureSetpointSetShift.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTRoomTemperatureSetpointSetShift.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            (0xFF, 0x4E),
            # out of DPTTemperatureDifference2Byte's range
            RoomTemperatureSetpointsShift(comfort=-700_000.0),
            # encodes to the same bits as "not used" (0x7FFF)
            RoomTemperatureSetpointsShift(comfort=670760.0),
        ],
    )
    def test_wrong_value_to_knx(self, value: Any) -> None:
        """Test DPTRoomTemperatureSetpointSetShift parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTRoomTemperatureSetpointSetShift.to_knx(value)

    def test_wrong_value_from_knx(self) -> None:
        """Test DPTRoomTemperatureSetpointSetShift parsing with wrong payload length."""
        with pytest.raises(CouldNotParseTelegram):
            DPTRoomTemperatureSetpointSetShift.from_knx(DPTArray((0xFF, 0x4E)))

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema."""
        field_schema = {
            "type": "float",
            "required": False,
            "value_min": -670760.0,
            "value_max": 670760.0,
            "resolution": 0.01,
        }
        assert DPTRoomTemperatureSetpointSetShift.get_dict_schema() == [
            {"name": "comfort", **field_schema},
            {"name": "standby", **field_schema},
            {"name": "economy", **field_schema},
            {"name": "building_protection", **field_schema},
        ]
