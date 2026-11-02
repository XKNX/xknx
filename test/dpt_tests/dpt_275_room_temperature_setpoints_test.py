"""Unit test for KNX DPT 275 objects."""

from typing import Any

import pytest

from xknx.dpt import (
    DPTArray,
    DPTRoomTemperatureSetpoints4,
    DPTRoomTemperatureSetpointShifts4,
    RoomTemperatureSetpoints4,
    RoomTemperatureSetpointShifts4,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestRoomTemperatureSetpoints4:
    """Test RoomTemperatureSetpoints4 class."""

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
                RoomTemperatureSetpoints4(21.0, 19.0, 16.0, 5.0),
            ),
            (
                {"comfort": 2, "standby": 0, "economy": -2, "building_protection": -5},
                RoomTemperatureSetpoints4(2.0, 0.0, -2.0, -5.0),
            ),
            ({"comfort": 21.0}, RoomTemperatureSetpoints4(comfort=21.0)),
            ({}, RoomTemperatureSetpoints4()),
            (
                {"comfort": None, "standby": 19.0},
                RoomTemperatureSetpoints4(standby=19.0),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: RoomTemperatureSetpoints4) -> None:
        """Test from_dict and as_dict methods."""
        test_value = RoomTemperatureSetpoints4.from_dict(data)
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
            {"comfort": 21.0, "eco": 17.0},
            21.0,
            None,
        ],
    )
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            RoomTemperatureSetpoints4.from_dict(data)


class TestDPTRoomTemperatureSetpoints4:
    """Test class for KNX DPTRoomTemperatureSetpoints4 objects (DPT 275.100)."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                RoomTemperatureSetpoints4(21.0, 19.0, 16.0, 5.0),
                (0x0C, 0x1A, 0x07, 0x6C, 0x06, 0x40, 0x01, 0xF4),
            ),
            (
                RoomTemperatureSetpoints4(0.0, 0.0, 0.0, 0.0),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                # all fields "not used"
                RoomTemperatureSetpoints4(),
                (0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
            (
                # only comfort set, rest "not used"
                RoomTemperatureSetpoints4(comfort=21.0),
                (0x0C, 0x1A, 0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
            (
                # largest encodable value - 0x7FFE, one below "not used"
                RoomTemperatureSetpoints4(comfort=670433.28),
                (0x7F, 0xFE, 0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
        ],
    )
    def test_value(
        self, value: RoomTemperatureSetpoints4, raw: tuple[int, ...]
    ) -> None:
        """Test DPTRoomTemperatureSetpoints4 parsing and streaming."""
        knx_value = DPTRoomTemperatureSetpoints4.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTRoomTemperatureSetpoints4.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test DPTRoomTemperatureSetpoints4 parsing from a dict."""
        value = {
            "comfort": 21.0,
            "standby": 19.0,
            "economy": 16.0,
            "building_protection": 5.0,
        }
        knx_value = DPTRoomTemperatureSetpoints4.to_knx(value)
        assert knx_value == DPTArray((0x0C, 0x1A, 0x07, 0x6C, 0x06, 0x40, 0x01, 0xF4))

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            (0xFF, 0x4E),
            RoomTemperatureSetpoints4(21.0, 19.0, 16.0, "a"),
            # below absolute zero - out of DPTTemperature's range
            RoomTemperatureSetpoints4(comfort=-300.0),
            # above value_max - 0x7FFF is reserved for invalid data
            RoomTemperatureSetpoints4(comfort=670760.0),
        ],
    )
    def test_wrong_value_to_knx(self, value: Any) -> None:
        """Test DPTRoomTemperatureSetpoints4 parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTRoomTemperatureSetpoints4.to_knx(value)

    def test_wrong_value_from_knx(self) -> None:
        """Test DPTRoomTemperatureSetpoints4 parsing with wrong payload length."""
        with pytest.raises(CouldNotParseTelegram):
            DPTRoomTemperatureSetpoints4.from_knx(DPTArray((0xFF, 0x4E)))

    def test_from_knx_field_out_of_range(self) -> None:
        """Test one field outside DPTTemperature's range rejects the whole payload."""
        # standby 0xF800 is -671088.64 °C - only 0x7FFF means "not used"
        with pytest.raises(ConversionError):
            DPTRoomTemperatureSetpoints4.from_knx(
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
        assert DPTRoomTemperatureSetpoints4.get_dict_schema() == [
            {"name": "comfort", **field_schema},
            {"name": "standby", **field_schema},
            {"name": "economy", **field_schema},
            {"name": "building_protection", **field_schema},
        ]


class TestRoomTemperatureSetpointShifts4:
    """Test RoomTemperatureSetpointShifts4 class."""

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
                RoomTemperatureSetpointShifts4(2.5, 0.0, -2.5, -5.0),
            ),
            ({}, RoomTemperatureSetpointShifts4()),
        ],
    )
    def test_dict(
        self, data: dict[str, Any], value: RoomTemperatureSetpointShifts4
    ) -> None:
        """Test from_dict and as_dict methods."""
        test_value = RoomTemperatureSetpointShifts4.from_dict(data)
        assert test_value == value
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
            {"comfort_shift": 1.0},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            RoomTemperatureSetpointShifts4.from_dict(data)


class TestDPTRoomTemperatureSetpointShifts4:
    """Test class for KNX DPTRoomTemperatureSetpointShifts4 objects (DPT 275.101)."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                RoomTemperatureSetpointShifts4(2.5, 0.0, -2.5, -5.0),
                (0x00, 0xFA, 0x00, 0x00, 0x87, 0x06, 0x86, 0x0C),
            ),
            (
                RoomTemperatureSetpointShifts4(),
                (0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
            (
                # smallest and largest encodable value - 0xF800 and 0x7FFE
                RoomTemperatureSetpointShifts4(comfort=-671088.64, standby=670433.28),
                (0xF8, 0x00, 0x7F, 0xFE, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
        ],
    )
    def test_value(
        self, value: RoomTemperatureSetpointShifts4, raw: tuple[int, ...]
    ) -> None:
        """Test DPTRoomTemperatureSetpointShifts4 parsing and streaming."""
        knx_value = DPTRoomTemperatureSetpointShifts4.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTRoomTemperatureSetpointShifts4.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            (0xFF, 0x4E),
            # out of DPTTemperatureDifference2Byte's range
            RoomTemperatureSetpointShifts4(comfort=-700_000.0),
            # above value_max - 0x7FFF is reserved for invalid data
            RoomTemperatureSetpointShifts4(comfort=670760.0),
        ],
    )
    def test_wrong_value_to_knx(self, value: Any) -> None:
        """Test DPTRoomTemperatureSetpointShifts4 parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTRoomTemperatureSetpointShifts4.to_knx(value)

    def test_wrong_value_from_knx(self) -> None:
        """Test DPTRoomTemperatureSetpointShifts4 parsing with wrong payload length."""
        with pytest.raises(CouldNotParseTelegram):
            DPTRoomTemperatureSetpointShifts4.from_knx(DPTArray((0xFF, 0x4E)))

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema."""
        field_schema = {
            "type": "float",
            "required": False,
            "value_min": -671088.64,
            "value_max": 670433.28,
            "resolution": 0.01,
        }
        assert DPTRoomTemperatureSetpointShifts4.get_dict_schema() == [
            {"name": "comfort", **field_schema},
            {"name": "standby", **field_schema},
            {"name": "economy", **field_schema},
            {"name": "building_protection", **field_schema},
        ]
