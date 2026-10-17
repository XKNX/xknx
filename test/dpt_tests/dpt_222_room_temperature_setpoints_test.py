"""Unit test for KNX DPT 222 objects."""

from typing import Any

import pytest

from xknx.dpt import (
    DPTArray,
    DPTBase,
    DPTBinary,
    DPTRoomTemperatureSetpoints,
    DPTRoomTemperatureSetpointShifts,
    RoomTemperatureSetpoints,
    RoomTemperatureSetpointShifts,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestRoomTemperatureSetpoints:
    """Test RoomTemperatureSetpoints and RoomTemperatureSetpointShifts classes."""

    @pytest.mark.parametrize(
        "data_class", [RoomTemperatureSetpoints, RoomTemperatureSetpointShifts]
    )
    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (
                {"comfort": 21.0, "standby": 18.5, "economy": 16},
                (21.0, 18.5, 16.0),
            ),
            ({"comfort": "21.5"}, (21.5, None, None)),
            ({"standby": 0}, (None, 0.0, None)),
            ({"economy": -1.5, "comfort": None}, (None, None, -1.5)),
            ({}, (None, None, None)),
        ],
    )
    def test_dict(
        self,
        data_class: type[RoomTemperatureSetpoints | RoomTemperatureSetpointShifts],
        data: dict[str, Any],
        expected: tuple[float | None, float | None, float | None],
    ) -> None:
        """Test from_dict and as_dict methods."""
        value = data_class.from_dict(data)
        assert value == data_class(*expected)
        assert value.as_dict() == dict(
            zip(("comfort", "standby", "economy"), expected, strict=True)
        )

    @pytest.mark.parametrize(
        "data_class", [RoomTemperatureSetpoints, RoomTemperatureSetpointShifts]
    )
    @pytest.mark.parametrize(
        "data",
        [
            {"comfort": "a"},
            {"standby": [21]},
            {"economy": {}},
        ],
    )
    def test_dict_invalid(
        self,
        data_class: type[RoomTemperatureSetpoints | RoomTemperatureSetpointShifts],
        data: dict[str, Any],
    ) -> None:
        """Test from_dict with invalid values."""
        with pytest.raises(ValueError):
            data_class.from_dict(data)


class TestDPTRoomTemperatureSetpoints:
    """Test class for KNX DPTRoomTemperatureSetpoints objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                RoomTemperatureSetpoints(0, 0, 0),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                RoomTemperatureSetpoints(21.0, 18.5, 16.0),
                (0x0C, 0x1A, 0x07, 0x3A, 0x06, 0x40),
            ),
            (
                RoomTemperatureSetpoints(-1.5, 0.5, 670433.28),
                (0x87, 0x6A, 0x00, 0x32, 0x7F, 0xFE),
            ),
            # -273 is not representable; it encodes to the nearest value -272.96
            (
                RoomTemperatureSetpoints(-272.96, 0, 0),
                (0xA1, 0x56, 0x00, 0x00, 0x00, 0x00),
            ),
            # 7FFFh denotes invalid data
            (
                RoomTemperatureSetpoints(None, 18.5, 16.0),
                (0x7F, 0xFF, 0x07, 0x3A, 0x06, 0x40),
            ),
            (
                RoomTemperatureSetpoints(21.0, None, 16.0),
                (0x0C, 0x1A, 0x7F, 0xFF, 0x06, 0x40),
            ),
            (
                RoomTemperatureSetpoints(21.0, 18.5, None),
                (0x0C, 0x1A, 0x07, 0x3A, 0x7F, 0xFF),
            ),
            (
                RoomTemperatureSetpoints(),
                (0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
        ],
    )
    def test_values(
        self, value: RoomTemperatureSetpoints, raw: tuple[int, ...]
    ) -> None:
        """Test parsing and streaming."""
        knx_value = DPTRoomTemperatureSetpoints.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTRoomTemperatureSetpoints.from_knx(knx_value) == value

    def test_to_knx_lower_limit(self) -> None:
        """Test -273 encodes to its nearest representable value."""
        assert DPTRoomTemperatureSetpoints.to_knx(
            RoomTemperatureSetpoints(-273, -273, -273)
        ) == DPTArray((0xA1, 0x56, 0xA1, 0x56, 0xA1, 0x56))

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                {"comfort": 21, "standby": 18.5, "economy": "16"},
                (0x0C, 0x1A, 0x07, 0x3A, 0x06, 0x40),
            ),
            ({"standby": 18.5}, (0x7F, 0xFF, 0x07, 0x3A, 0x7F, 0xFF)),
        ],
    )
    def test_to_knx_from_dict(
        self, value: dict[str, Any], raw: tuple[int, ...]
    ) -> None:
        """Test serializing from a dict."""
        assert DPTRoomTemperatureSetpoints.to_knx(value) == DPTArray(raw)

    @pytest.mark.parametrize(
        "value",
        [
            RoomTemperatureSetpoints(-273.01, 0, 0),
            RoomTemperatureSetpoints(0, 670433.29, 0),
            RoomTemperatureSetpoints(0, 0, float("nan")),
            RoomTemperatureSetpoints(0, 0, float("inf")),
            RoomTemperatureSetpoints(comfort="a"),  # type: ignore[arg-type]
            {"comfort": "a"},
            {"economy": -300},
            None,
            1,
            (0x0C, 0x1A),
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTRoomTemperatureSetpoints.to_knx(value)

    def test_from_knx_below_range(self) -> None:
        """Test parsing a setpoint below -273 °C."""
        # A154h decodes to -273.28
        with pytest.raises(ConversionError):
            DPTRoomTemperatureSetpoints.from_knx(
                DPTArray((0x00, 0x00, 0xA1, 0x54, 0x00, 0x00))
            )

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x0C, 0x1A, 0x07, 0x3A, 0x06)),
            DPTArray((0x0C, 0x1A, 0x07, 0x3A, 0x06, 0x40, 0x00)),
            DPTBinary(1),
        ],
    )
    def test_from_knx_invalid_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing payloads of wrong length or type."""
        with pytest.raises(CouldNotParseTelegram):
            DPTRoomTemperatureSetpoints.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema."""
        assert DPTRoomTemperatureSetpoints.get_dict_schema() == [
            {
                "name": name,
                "type": "float",
                "required": False,
                "value_min": -273,
                "value_max": 670433.28,
                "resolution": 0.01,
            }
            for name in ("comfort", "standby", "economy")
        ]

    @pytest.mark.parametrize("value_type", ["222.100", "room_temperature_setpoints"])
    def test_parse_transcoder(self, value_type: str) -> None:
        """Test lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder(value_type) is DPTRoomTemperatureSetpoints


class TestDPTRoomTemperatureSetpointShifts:
    """Test class for KNX DPTRoomTemperatureSetpointShifts objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                RoomTemperatureSetpointShifts(0, 0, 0),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                RoomTemperatureSetpointShifts(-1.5, 0.5, 1.0),
                (0x87, 0x6A, 0x00, 0x32, 0x00, 0x64),
            ),
            (
                RoomTemperatureSetpointShifts(-671088.64, 670433.28, -300.0),
                (0xF8, 0x00, 0x7F, 0xFE, 0xA0, 0xAD),
            ),
            # 7FFFh denotes invalid data
            (
                RoomTemperatureSetpointShifts(None, 0.5, 1.0),
                (0x7F, 0xFF, 0x00, 0x32, 0x00, 0x64),
            ),
            (
                RoomTemperatureSetpointShifts(-1.5, None, 1.0),
                (0x87, 0x6A, 0x7F, 0xFF, 0x00, 0x64),
            ),
            (
                RoomTemperatureSetpointShifts(-1.5, 0.5, None),
                (0x87, 0x6A, 0x00, 0x32, 0x7F, 0xFF),
            ),
            (
                RoomTemperatureSetpointShifts(),
                (0x7F, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
        ],
    )
    def test_values(
        self, value: RoomTemperatureSetpointShifts, raw: tuple[int, ...]
    ) -> None:
        """Test parsing and streaming."""
        knx_value = DPTRoomTemperatureSetpointShifts.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTRoomTemperatureSetpointShifts.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test serializing from a dict."""
        assert DPTRoomTemperatureSetpointShifts.to_knx(
            {"comfort": "-1.5", "economy": 1}
        ) == DPTArray((0x87, 0x6A, 0x7F, 0xFF, 0x00, 0x64))

    @pytest.mark.parametrize(
        "value",
        [
            RoomTemperatureSetpointShifts(-671088.65, 0, 0),
            RoomTemperatureSetpointShifts(0, 670433.29, 0),
            RoomTemperatureSetpointShifts(0, 0, float("nan")),
            {"standby": "a"},
            None,
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTRoomTemperatureSetpointShifts.to_knx(value)

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x87, 0x6A, 0x00, 0x32)),
            DPTArray((0x87, 0x6A, 0x00, 0x32, 0x00, 0x64, 0x00)),
            DPTBinary(0),
        ],
    )
    def test_from_knx_invalid_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing payloads of wrong length or type."""
        with pytest.raises(CouldNotParseTelegram):
            DPTRoomTemperatureSetpointShifts.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema."""
        assert DPTRoomTemperatureSetpointShifts.get_dict_schema() == [
            {
                "name": name,
                "type": "float",
                "required": False,
                "value_min": -671088.64,
                "value_max": 670433.28,
                "resolution": 0.01,
            }
            for name in ("comfort", "standby", "economy")
        ]

    @pytest.mark.parametrize(
        "value_type", ["222.101", "room_temperature_setpoint_shifts"]
    )
    def test_parse_transcoder(self, value_type: str) -> None:
        """Test lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder(value_type) is DPTRoomTemperatureSetpointShifts
