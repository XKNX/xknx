"""Unit test for KNX DPT 246 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_246 import BatteryInfo, DPTBatteryInfo
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestBatteryInfo:
    """Test BatteryInfo class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {
                    "battery_failure": False,
                    "battery_duration_failure": False,
                    "battery_fully_charged": True,
                    "charge_level": 254,
                },
                BatteryInfo(False, False, True, 254),
            ),
            (
                {
                    "battery_failure": True,
                    "battery_duration_failure": True,
                    "battery_fully_charged": False,
                },
                BatteryInfo(True, True, False, None),
            ),
            (
                {
                    "battery_failure": False,
                    "battery_duration_failure": True,
                    "battery_fully_charged": False,
                    "charge_level": None,
                },
                BatteryInfo(False, True, False, None),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: BatteryInfo) -> None:
        """Test from_dict and as_dict methods."""
        assert BatteryInfo.from_dict(data) == value
        default_dict = {"charge_level": None}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"battery_failure": False, "battery_duration_failure": False},
            {
                "battery_failure": 1,
                "battery_duration_failure": False,
                "battery_fully_charged": False,
            },
            {
                "battery_failure": False,
                "battery_duration_failure": "no",
                "battery_fully_charged": False,
            },
            {
                "battery_failure": False,
                "battery_duration_failure": False,
                "battery_fully_charged": None,
            },
            {
                "battery_failure": False,
                "battery_duration_failure": False,
                "battery_fully_charged": False,
                "charge_level": "a",
            },
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            BatteryInfo.from_dict(data)


class TestDPTBatteryInfo:
    """Test class for KNX DPTBatteryInfo objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (BatteryInfo(False, False, False, 0), (0x00, 0x00)),
            (BatteryInfo(False, False, False, None), (0x00, 0xFF)),
            (BatteryInfo(True, False, False, 128), (0x01, 0x80)),
            (BatteryInfo(False, True, False, 1), (0x02, 0x01)),
            (BatteryInfo(False, False, True, 254), (0x04, 0xFE)),
            (BatteryInfo(True, True, True, None), (0x07, 0xFF)),
        ],
    )
    def test_to_knx_from_knx(self, value: BatteryInfo, raw: tuple[int, ...]) -> None:
        """Test DPTBatteryInfo parsing and streaming."""
        knx_value = DPTBatteryInfo.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTBatteryInfo.from_knx(knx_value) == value
        assert DPTBatteryInfo.to_knx(value.as_dict()) == DPTArray(raw)

    def test_reserved_bits_ignored(self) -> None:
        """Test reserved bits are ignored on receive."""
        assert DPTBatteryInfo.from_knx(DPTArray((0xF9, 0x10))) == BatteryInfo(
            True, False, False, 16
        )

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00,)),
            DPTArray((0x00, 0x00, 0x00)),
            DPTBinary(0),
        ],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing invalid payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTBatteryInfo.from_knx(payload)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            {"battery_failure": False},
            BatteryInfo(False, False, False, -1),
            BatteryInfo(False, False, False, 255),
            BatteryInfo(False, False, False, "a"),  # type: ignore[arg-type]
        ],
    )
    def test_to_knx_wrong_value(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTBatteryInfo.to_knx(value)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTBatteryInfo."""
        assert DPTBatteryInfo.get_dict_schema() == [
            {"name": "battery_failure", "type": "boolean", "required": True},
            {"name": "battery_duration_failure", "type": "boolean", "required": True},
            {"name": "battery_fully_charged", "type": "boolean", "required": True},
            {
                "name": "charge_level",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 254,
            },
        ]

    def test_lookup(self) -> None:
        """Test transcoder lookup by DPT number and value type."""
        assert DPTBase.parse_transcoder("246.600") is DPTBatteryInfo
        assert DPTBase.parse_transcoder("battery_info") is DPTBatteryInfo
