"""Unit test for KNX DPT 272 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_248 import ConverterInfoValid
from xknx.dpt.dpt_272 import ConverterInfo, DPTConverterInfo
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestConverterInfo:
    """Test ConverterInfo class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {
                    "info_valid": "valid",
                    "lamp_emergency_time": 12,
                    "lamp_total_operation_time": 40_000,
                    "emergency_level": 200,
                    "short_address": 63,
                },
                ConverterInfo(ConverterInfoValid.VALID, 12, 40_000, 200, 63),
            ),
            (
                {
                    "info_valid": "not_available",
                    "lamp_emergency_time": 0,
                    "lamp_total_operation_time": 0,
                    "short_address": 0,
                },
                ConverterInfo(ConverterInfoValid.NOT_AVAILABLE, 0, 0, None, 0),
            ),
            (
                {
                    "info_valid": "invalid",
                    "lamp_emergency_time": 1,
                    "lamp_total_operation_time": 2,
                    "emergency_level": None,
                    "short_address": 3,
                },
                ConverterInfo(ConverterInfoValid.INVALID, 1, 2, None, 3),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: ConverterInfo) -> None:
        """Test from_dict and as_dict methods."""
        assert ConverterInfo.from_dict(data) == value
        default_dict = {"emergency_level": None}
        assert value.as_dict() == default_dict | data

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {
                "info_valid": "valid",
                "lamp_emergency_time": 0,
                "lamp_total_operation_time": 0,
            },
            {
                "info_valid": "maybe",
                "lamp_emergency_time": 0,
                "lamp_total_operation_time": 0,
                "short_address": 0,
            },
            {
                "info_valid": 3,
                "lamp_emergency_time": 0,
                "lamp_total_operation_time": 0,
                "short_address": 0,
            },
            {
                "info_valid": "valid",
                "lamp_emergency_time": "a",
                "lamp_total_operation_time": 0,
                "short_address": 0,
            },
            {
                "info_valid": "valid",
                "lamp_emergency_time": 0,
                "lamp_total_operation_time": None,
                "short_address": 0,
            },
            {
                "info_valid": "valid",
                "lamp_emergency_time": 0,
                "lamp_total_operation_time": 0,
                "emergency_level": "a",
                "short_address": 0,
            },
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            ConverterInfo.from_dict(data)


class TestDPTConverterInfo:
    """Test class for KNX DPTConverterInfo objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                ConverterInfo(ConverterInfoValid.NOT_AVAILABLE, 0, 0, None, 0),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0x00),
            ),
            (
                ConverterInfo(ConverterInfoValid.VALID, 0, 0, 0, 0),
                (0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                ConverterInfo(ConverterInfoValid.VALID, 0x1234, 0xABCD, 128, 17),
                (0x01, 0x12, 0x34, 0xAB, 0xCD, 0x80, 0x11),
            ),
            (
                ConverterInfo(ConverterInfoValid.INVALID, 65_535, 65_535, 254, 63),
                (0x02, 0xFF, 0xFF, 0xFF, 0xFF, 0xFE, 0x3F),
            ),
        ],
    )
    def test_to_knx_from_knx(self, value: ConverterInfo, raw: tuple[int, ...]) -> None:
        """Test DPTConverterInfo parsing and streaming."""
        knx_value = DPTConverterInfo.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTConverterInfo.from_knx(knx_value) == value
        assert DPTConverterInfo.to_knx(value.as_dict()) == DPTArray(raw)

    @pytest.mark.parametrize(
        "raw",
        [
            (0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),  # reserved InfoValid
            (0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),  # reserved InfoValid
            (0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x40),  # short address 64
            (0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF),  # short address 255
        ],
    )
    def test_from_knx_invalid_values(self, raw: tuple[int, ...]) -> None:
        """Test parsing reserved or not allowed values."""
        with pytest.raises(ConversionError):
            DPTConverterInfo.from_knx(DPTArray(raw))

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00,) * 6),
            DPTArray((0x00,) * 8),
            DPTBinary(0),
        ],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing invalid payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTConverterInfo.from_knx(payload)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            1,
            {"info_valid": "valid"},
            ConverterInfo(ConverterInfoValid.VALID, -1, 0, 0, 0),
            ConverterInfo(ConverterInfoValid.VALID, 65_536, 0, 0, 0),
            ConverterInfo(ConverterInfoValid.VALID, 0, -1, 0, 0),
            ConverterInfo(ConverterInfoValid.VALID, 0, 65_536, 0, 0),
            ConverterInfo(ConverterInfoValid.VALID, 0, 0, -1, 0),
            ConverterInfo(ConverterInfoValid.VALID, 0, 0, 255, 0),
            ConverterInfo(ConverterInfoValid.VALID, 0, 0, 0, -1),
            ConverterInfo(ConverterInfoValid.VALID, 0, 0, 0, 64),
            ConverterInfo("valid", 0, 0, 0, 0),  # type: ignore[arg-type]
        ],
    )
    def test_to_knx_wrong_value(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTConverterInfo.to_knx(value)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTConverterInfo."""
        assert DPTConverterInfo.get_dict_schema() == [
            {
                "name": "info_valid",
                "type": "enum",
                "required": True,
                "options": ["not_available", "valid", "invalid"],
            },
            {
                "name": "lamp_emergency_time",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 65_535,
            },
            {
                "name": "lamp_total_operation_time",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 65_535,
            },
            {
                "name": "emergency_level",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 254,
            },
            {
                "name": "short_address",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 63,
            },
        ]

    def test_lookup(self) -> None:
        """Test transcoder lookup by DPT number and value type."""
        assert DPTBase.parse_transcoder("272.600") is DPTConverterInfo
        assert DPTBase.parse_transcoder("converter_info") is DPTConverterInfo
