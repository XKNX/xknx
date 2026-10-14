"""Unit test for KNX DPT 237 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_237 import (
    DALIAddressIndicator,
    DALIControlGearDiagnostic,
    DPTDALIControlGearDiagnostic,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram

DEFAULT_DICT = {
    "address_indicator": "device",
    "read_request": False,
    "lamp_failure": False,
    "ballast_failure": False,
    "converter_error": False,
}


class TestDALIControlGearDiagnostic:
    """Test DALIControlGearDiagnostic class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            ({"address": 0}, DALIControlGearDiagnostic(0)),
            (
                {"address": 63, "address_indicator": "device", "lamp_failure": True},
                DALIControlGearDiagnostic(63, lamp_failure=True),
            ),
            (
                {
                    "address": 15,
                    "address_indicator": "group",
                    "read_request": True,
                    "lamp_failure": True,
                    "ballast_failure": True,
                    "converter_error": True,
                },
                DALIControlGearDiagnostic(
                    15, DALIAddressIndicator.GROUP, True, True, True, True
                ),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: DALIControlGearDiagnostic) -> None:
        """Test from_dict and as_dict methods."""
        assert DALIControlGearDiagnostic.from_dict(data) == value
        assert value.as_dict() == DEFAULT_DICT | data

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"address": "a"},
            {"address": None},
            {"address": 1, "address_indicator": "invalid"},
            {"address": 1, "address_indicator": 2},
            {"address": 1, "read_request": "a"},
            {"address": 1, "lamp_failure": None},
            {"address": 1, "ballast_failure": 2},
            {"address": 1, "converter_error": "true"},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            DALIControlGearDiagnostic.from_dict(data)


class TestDPTDALIControlGearDiagnostic:
    """Test class for KNX DPTDALIControlGearDiagnostic objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (DALIControlGearDiagnostic(0), (0x00, 0x00)),
            (DALIControlGearDiagnostic(63), (0x00, 0x3F)),
            (DALIControlGearDiagnostic(0, DALIAddressIndicator.GROUP), (0x00, 0x40)),
            (DALIControlGearDiagnostic(15, DALIAddressIndicator.GROUP), (0x00, 0x4F)),
            (DALIControlGearDiagnostic(0, read_request=True), (0x00, 0x80)),
            (DALIControlGearDiagnostic(0, lamp_failure=True), (0x01, 0x00)),
            (DALIControlGearDiagnostic(0, ballast_failure=True), (0x02, 0x00)),
            (DALIControlGearDiagnostic(0, converter_error=True), (0x04, 0x00)),
            (
                DALIControlGearDiagnostic(
                    15, DALIAddressIndicator.GROUP, True, True, True, True
                ),
                (0x07, 0xCF),
            ),
            (DALIControlGearDiagnostic(42, lamp_failure=True), (0x01, 0x2A)),
        ],
    )
    def test_values(
        self, value: DALIControlGearDiagnostic, raw: tuple[int, ...]
    ) -> None:
        """Test parsing and streaming."""
        knx_value = DPTDALIControlGearDiagnostic.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTDALIControlGearDiagnostic.from_knx(knx_value) == value

    def test_from_knx_reserved_bits_ignored(self) -> None:
        """Test reserved bits b11..b15 are ignored on receive."""
        assert DPTDALIControlGearDiagnostic.from_knx(
            DPTArray((0xF9, 0x05))
        ) == DALIControlGearDiagnostic(5, lamp_failure=True)

    @pytest.mark.parametrize("raw", [(0x00, 0x50), (0x00, 0x7F), (0x00, 0xD0)])
    def test_from_knx_group_address_out_of_range(self, raw: tuple[int, ...]) -> None:
        """Test parsing group addresses above 15."""
        with pytest.raises(ConversionError):
            DPTDALIControlGearDiagnostic.from_knx(DPTArray(raw))

    def test_to_knx_from_dict(self) -> None:
        """Test serializing from a dict."""
        assert DPTDALIControlGearDiagnostic.to_knx(
            {"address": 3, "address_indicator": "group", "ballast_failure": True}
        ) == DPTArray((0x02, 0x43))

    @pytest.mark.parametrize(
        "value",
        [
            DALIControlGearDiagnostic(-1),
            DALIControlGearDiagnostic(64),
            DALIControlGearDiagnostic(16, DALIAddressIndicator.GROUP),
            DALIControlGearDiagnostic("a"),  # type: ignore[arg-type]
            {"address": 64},
            {"address": 16, "address_indicator": "group"},
            {"address_indicator": "group"},
            None,
            1,
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTDALIControlGearDiagnostic.to_knx(value)

    @pytest.mark.parametrize(
        "payload", [DPTArray(()), DPTArray((0x00,)), DPTArray((0, 0, 0)), DPTBinary(1)]
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test parsing wrong payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTDALIControlGearDiagnostic.from_knx(payload)

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema."""
        assert DPTDALIControlGearDiagnostic.get_dict_schema() == [
            {
                "name": "address",
                "type": "integer",
                "required": True,
                "value_min": 0,
                "value_max": 63,
            },
            {
                "name": "address_indicator",
                "type": "enum",
                "required": False,
                "default": "device",
                "options": ["device", "group"],
            },
            {
                "name": "read_request",
                "type": "boolean",
                "required": False,
                "default": False,
            },
            {
                "name": "lamp_failure",
                "type": "boolean",
                "required": False,
                "default": False,
            },
            {
                "name": "ballast_failure",
                "type": "boolean",
                "required": False,
                "default": False,
            },
            {
                "name": "converter_error",
                "type": "boolean",
                "required": False,
                "default": False,
            },
        ]

    def test_transcoder_lookup(self) -> None:
        """Test lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder("237.600") is DPTDALIControlGearDiagnostic
        assert (
            DPTBase.parse_transcoder("dali_control_gear_diagnostic")
            is DPTDALIControlGearDiagnostic
        )
