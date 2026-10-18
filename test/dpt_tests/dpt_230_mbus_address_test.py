"""Unit test for KNX DPT 230 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary, DPTComplex
from xknx.dpt.dpt_20 import MeteringDeviceType
from xknx.dpt.dpt_230 import DPTMBusAddress, MBusAddress
from xknx.exceptions import ConversionError, CouldNotParseTelegram

_SUPPORTED_MEDIA = {
    0x00,
    0x01,
    0x02,
    0x03,
    0x04,
    0x05,
    0x06,
    0x07,
    0x08,
    0x0A,
    0x0B,
    0x0C,
    0x0D,
    0x20,
    0x21,
    0x28,
    0x29,
    0xFF,
}


class TestMBusAddress:
    """Test MBusAddress class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {
                    "manufacturer_id": 0x2C2D,
                    "identification_number": 12345678,
                    "version": 1,
                    "medium": "heat_meter",
                },
                MBusAddress(0x2C2D, 12345678, 1, MeteringDeviceType.HEAT_METER),
            ),
            (
                {
                    "manufacturer_id": 65535,
                    "identification_number": 4_294_967_295,
                    "version": 255,
                    "medium": "garbage",
                },
                MBusAddress(65535, 4_294_967_295, 255, MeteringDeviceType.GARBAGE),
            ),
            (
                {
                    "manufacturer_id": 1,
                    "identification_number": 2,
                    "version": 3,
                    "medium": 0x15,
                },
                MBusAddress(1, 2, 3, 0x15),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: MBusAddress) -> None:
        """Test from_dict and as_dict methods."""
        assert MBusAddress.from_dict(data) == value
        assert value.as_dict() == data

    def test_dict_medium_code(self) -> None:
        """Test a listed medium given as code is parsed to the Enum."""
        assert MBusAddress.from_dict(
            {
                "manufacturer_id": 1,
                "identification_number": 2,
                "version": 3,
                "medium": 7,
            }
        ) == MBusAddress(1, 2, 3, MeteringDeviceType.WATER_METER)

    @pytest.mark.parametrize(
        "data",
        [
            {"identification_number": 0, "version": 0, "medium": "other"},
            {"manufacturer_id": 0, "version": 0, "medium": "other"},
            {"manufacturer_id": 0, "identification_number": 0, "medium": "other"},
            {"manufacturer_id": 0, "identification_number": 0, "version": 0},
            {
                "manufacturer_id": "a",
                "identification_number": 0,
                "version": 0,
                "medium": "other",
            },
            {
                "manufacturer_id": 0,
                "identification_number": None,
                "version": 0,
                "medium": "other",
            },
            {
                "manufacturer_id": 0,
                "identification_number": 0,
                "version": 0,
                "medium": "invalid",
            },
            {
                "manufacturer_id": 0,
                "identification_number": 0,
                "version": 0,
                "medium": True,
            },
            {
                "manufacturer_id": 0,
                "identification_number": 0,
                "version": 0,
                "medium": None,
            },
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid values."""
        with pytest.raises(ValueError):
            MBusAddress.from_dict(data)


class TestDPTMBusAddress:
    """Test class for KNX DPTMBusAddress objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                MBusAddress(0, 0, 0, MeteringDeviceType.OTHER),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                MBusAddress(65535, 4_294_967_295, 255, MeteringDeviceType.GARBAGE),
                (0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x29),
            ),
            (
                MBusAddress(0x2C2D, 0x12345678, 0x1B, MeteringDeviceType.WATER_METER),
                (0x2C, 0x2D, 0x12, 0x34, 0x56, 0x78, 0x1B, 0x07),
            ),
        ],
    )
    def test_round_trip(self, value: MBusAddress, raw: tuple[int, ...]) -> None:
        """Test DPTMBusAddress parsing and streaming."""
        knx_value = DPTMBusAddress.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTMBusAddress.from_knx(knx_value) == value

    @pytest.mark.parametrize("medium", list(MeteringDeviceType))
    def test_medium(self, medium: MeteringDeviceType) -> None:
        """Test every medium value."""
        payload = DPTArray((0x00, 0x01, 0x00, 0x00, 0x00, 0x02, 0x03, medium.value))
        value = MBusAddress(1, 2, 3, medium)
        assert DPTMBusAddress.from_knx(payload) == value
        assert DPTMBusAddress.to_knx(value) == payload

    def test_supported_media(self) -> None:
        """Test the Enum holds exactly the media of DPT 20.114."""
        assert {medium.value for medium in MeteringDeviceType} == _SUPPORTED_MEDIA

    @pytest.mark.parametrize("code", sorted(set(range(256)) - _SUPPORTED_MEDIA))
    def test_unlisted_medium(self, code: int) -> None:
        """Test a medium code the KNX table does not list is kept as int."""
        payload = DPTArray((0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, code))
        value = DPTMBusAddress.from_knx(payload)
        assert value == MBusAddress(0, 0, 0, code)
        assert value.as_dict()["medium"] == code
        assert DPTMBusAddress.to_knx(value) == payload

    def test_to_knx_from_dict(self) -> None:
        """Test DPTMBusAddress serializing from a dict."""
        assert DPTMBusAddress.to_knx(
            {
                "manufacturer_id": 0x0442,
                "identification_number": 0x99999999,
                "version": 0x30,
                "medium": "electricity_meter",
            }
        ) == DPTArray((0x04, 0x42, 0x99, 0x99, 0x99, 0x99, 0x30, 0x02))

    @pytest.mark.parametrize(
        "value",
        [
            MBusAddress(-1, 0, 0, MeteringDeviceType.OTHER),
            MBusAddress(65536, 0, 0, MeteringDeviceType.OTHER),
            MBusAddress(0, -1, 0, MeteringDeviceType.OTHER),
            MBusAddress(0, 4_294_967_296, 0, MeteringDeviceType.OTHER),
            MBusAddress(0, 0, -1, MeteringDeviceType.OTHER),
            MBusAddress(0, 0, 256, MeteringDeviceType.OTHER),
            MBusAddress("a", 0, 0, MeteringDeviceType.OTHER),  # type: ignore[arg-type]
            MBusAddress(0, 1.5, 0, MeteringDeviceType.OTHER),  # type: ignore[arg-type]
            MBusAddress(0, 0, 0, 256),
            MBusAddress(0, 0, 0, -1),
            MBusAddress(0, 0, 0, True),
            MBusAddress(0, 0, 0, "other"),  # type: ignore[arg-type]
            {
                "manufacturer_id": 0,
                "identification_number": 0,
                "version": 256,
                "medium": "other",
            },
            {"manufacturer_id": 0},
            None,
            1,
            (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test DPTMBusAddress serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTMBusAddress.to_knx(value)

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)),
            DPTArray((0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)),
            DPTBinary(1),
        ],
    )
    def test_from_knx_invalid_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test DPTMBusAddress parsing invalid payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTMBusAddress.from_knx(payload)

    @pytest.mark.parametrize("value_type", ["230.1000", "mbus_address"])
    def test_lookup(self, value_type: str) -> None:
        """Test transcoder lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder(value_type) is DPTMBusAddress
        assert DPTComplex.parse_transcoder(value_type) is DPTMBusAddress
        assert DPTBase.parse_transcoder({"main": 230, "sub": 1000}) is DPTMBusAddress

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTMBusAddress."""
        assert DPTMBusAddress.get_dict_schema() == [
            {
                "name": "manufacturer_id",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 65535,
            },
            {
                "name": "identification_number",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 4_294_967_295,
            },
            {
                "name": "version",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 255,
            },
            {
                "name": "medium",
                "type": "enum",
                "required": True,
                "options": [
                    "other",
                    "oil_meter",
                    "electricity_meter",
                    "gas_meter",
                    "heat_meter",
                    "steam_meter",
                    "warm_water_meter",
                    "water_meter",
                    "heat_cost_allocator",
                    "cooling_load_meter_outlet",
                    "cooling_load_meter_inlet",
                    "heat_inlet",
                    "heat_and_cool",
                    "breaker",
                    "valve",
                    "waste_water_meter",
                    "garbage",
                    "void",
                ],
            },
        ]
