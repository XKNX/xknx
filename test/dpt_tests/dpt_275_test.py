"""Unit test for KNX DPT 275 objects."""

from typing import Any

import pytest

from xknx.dpt import (
    DPTArray,
    DPTRoomTemperatureSetpointSet,
    DPTRoomTemperatureSetpointShiftSet,
    RoomTemperatureSetpoints,
    RoomTemperatureSetpointShifts,
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
            (
                # largest encodable value - 0x7FFE, one below "not used"
                RoomTemperatureSetpoints(comfort=670433.28),
                (0x7F, 0xFE, 0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF),
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
            # above value_max - 0x7FFF is reserved for invalid data
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

    def test_from_knx_field_out_of_range(self) -> None:
        """Test one field outside DPTTemperature's range rejects the whole payload."""
        # standby 0xF800 is -671088.64 °C - only 0x7FFF means "not used"
        with pytest.raises(ConversionError):
            DPTRoomTemperatureSetpointSet.from_knx(
                DPTArray((0x0C, 0x1A, 0xF8, 0x00, 0x7F, 0xFF, 0x7F, 0xFF))
            )

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema."""
        field_schema = {
            "type": "float",
            "required": False,
            "value_min": -273.0,
            "value_max": 670433.28,
            "resolution": 0.01,
        }
        assert DPTRoomTemperatureSetpointSet.get_dict_schema() == [
            {"name": "comfort", **field_schema},
            {"name": "standby", **field_schema},
            {"name": "economy", **field_schema},
            {"name": "building_protection", **field_schema},
        ]


class TestRoomTemperatureSetpointShifts:
    """Test RoomTemperatureSetpointShifts class."""

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
                RoomTemperatureSetpointShifts(2.5, 0.0, -2.5, -5.0),
            ),
            ({}, RoomTemperatureSetpointShifts()),
        ],
    )
    def test_dict(
        self, data: dict[str, Any], value: RoomTemperatureSetpointShifts
    ) -> None:
        """Test from_dict and as_dict methods."""
        test_value = RoomTemperatureSetpointShifts.from_dict(data)
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
            RoomTemperatureSetpointShifts.from_dict({"comfort": "a"})


class TestDPTRoomTemperatureSetpointShiftSet:
    """Test class for KNX DPTRoomTemperatureSetpointShiftSet objects (DPT 275.101)."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                RoomTemperatureSetpointShifts(2.5, 0.0, -2.5, -5.0),
                (0x00, 0xFA, 0x00, 0x00, 0x87, 0x06, 0x86, 0x0C),
            ),
            (
                RoomTemperatureSetpointShifts(),
                (0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
            (
                # smallest and largest encodable value - 0xF800 and 0x7FFE
                RoomTemperatureSetpointShifts(comfort=-671088.64, standby=670433.28),
                (0xF8, 0x00, 0x7F, 0xFE, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
        ],
    )
    def test_value(
        self, value: RoomTemperatureSetpointShifts, raw: tuple[int, ...]
    ) -> None:
        """Test DPTRoomTemperatureSetpointShiftSet parsing and streaming."""
        knx_value = DPTRoomTemperatureSetpointShiftSet.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTRoomTemperatureSetpointShiftSet.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            (0xFF, 0x4E),
            # out of DPTTemperatureDifference2Byte's range
            RoomTemperatureSetpointShifts(comfort=-700_000.0),
            # above value_max - 0x7FFF is reserved for invalid data
            RoomTemperatureSetpointShifts(comfort=670760.0),
        ],
    )
    def test_wrong_value_to_knx(self, value: Any) -> None:
        """Test DPTRoomTemperatureSetpointShiftSet parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTRoomTemperatureSetpointShiftSet.to_knx(value)

    def test_wrong_value_from_knx(self) -> None:
        """Test DPTRoomTemperatureSetpointShiftSet parsing with wrong payload length."""
        with pytest.raises(CouldNotParseTelegram):
            DPTRoomTemperatureSetpointShiftSet.from_knx(DPTArray((0xFF, 0x4E)))

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema."""
        field_schema = {
            "type": "float",
            "required": False,
            "value_min": -671088.64,
            "value_max": 670433.28,
            "resolution": 0.01,
        }
        assert DPTRoomTemperatureSetpointShiftSet.get_dict_schema() == [
            {"name": "comfort", **field_schema},
            {"name": "standby", **field_schema},
            {"name": "economy", **field_schema},
            {"name": "building_protection", **field_schema},
        ]
