"""Unit test for KNX DPT 229 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary, DPTComplex
from xknx.dpt.dpt_229 import DPTMeteringValue, MeteringValue, MeteringValueUnit
from xknx.exceptions import ConversionError, CouldNotParseTelegram

_STATUS_BITS = ("out_of_service", "fault", "overridden", "in_alarm", "alarm_un_ack")

# ValInfField code -> (unit, exponent) of KNX v02.02.01 - Datapoint Types 03.07.02 - §3.45.1
_CODES: list[tuple[int, MeteringValueUnit, int]] = [
    *((0x00 + n, MeteringValueUnit.ENERGY_WH, n - 3) for n in range(8)),
    *((0x80 + n, MeteringValueUnit.ENERGY_WH, n + 5) for n in range(2)),
    *((0x08 + n, MeteringValueUnit.ENERGY_J, n) for n in range(8)),
    *((0x88 + n, MeteringValueUnit.ENERGY_J, n + 8) for n in range(2)),
    *((0x10 + n, MeteringValueUnit.VOLUME_M3, n - 6) for n in range(8)),
    *((0x18 + n, MeteringValueUnit.MASS_KG, n - 3) for n in range(8)),
    *((0x28 + n, MeteringValueUnit.POWER_W, n - 3) for n in range(8)),
    *((0xA8 + n, MeteringValueUnit.POWER_W, n + 5) for n in range(2)),
    *((0x30 + n, MeteringValueUnit.POWER_J_PER_H, n) for n in range(8)),
    *((0xB0 + n, MeteringValueUnit.POWER_J_PER_H, n + 8) for n in range(2)),
    *((0x38 + n, MeteringValueUnit.VOLUME_FLOW_M3_PER_H, n - 6) for n in range(8)),
    *((0x40 + n, MeteringValueUnit.VOLUME_FLOW_M3_PER_MIN, n - 7) for n in range(8)),
    *((0x48 + n, MeteringValueUnit.VOLUME_FLOW_M3_PER_S, n - 9) for n in range(8)),
    *((0x50 + n, MeteringValueUnit.MASS_FLOW_KG_PER_H, n - 3) for n in range(8)),
    (0x6E, MeteringValueUnit.HCA_UNITS, 0),
    (0xBA, MeteringValueUnit.DIMENSIONLESS_COUNTER, 0),
]
_RESERVED_CODES = sorted(set(range(256)) - {code for code, _, _ in _CODES})


class TestMeteringValue:
    """Test MeteringValue class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {
                    "counter_value": 12345,
                    "unit": "energy_wh",
                    "exponent": 3,
                    "out_of_service": False,
                    "fault": False,
                    "overridden": True,
                    "in_alarm": False,
                    "alarm_un_ack": True,
                },
                MeteringValue(
                    12345,
                    MeteringValueUnit.ENERGY_WH,
                    3,
                    overridden=True,
                    alarm_un_ack=True,
                ),
            ),
            (
                {
                    "counter_value": -2_147_483_648,
                    "unit": "volume_flow_m3_per_s",
                    "exponent": -9,
                    "out_of_service": True,
                    "fault": True,
                    "overridden": False,
                    "in_alarm": True,
                    "alarm_un_ack": False,
                },
                MeteringValue(
                    -2_147_483_648,
                    MeteringValueUnit.VOLUME_FLOW_M3_PER_S,
                    -9,
                    out_of_service=True,
                    fault=True,
                    in_alarm=True,
                ),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: MeteringValue) -> None:
        """Test from_dict and as_dict methods."""
        assert MeteringValue.from_dict(data) == value
        assert value.as_dict() == data

    def test_dict_defaults(self) -> None:
        """Test from_dict with optional keys omitted."""
        assert MeteringValue.from_dict(
            {"counter_value": "7", "unit": "hca_units"}
        ) == MeteringValue(7, MeteringValueUnit.HCA_UNITS)

    @pytest.mark.parametrize(
        "data",
        [
            {"unit": "energy_wh"},
            {"counter_value": 0},
            {"counter_value": "a", "unit": "energy_wh"},
            {"counter_value": None, "unit": "energy_wh"},
            {"counter_value": 0, "unit": "invalid"},
            {"counter_value": 0, "unit": "energy_wh", "exponent": "a"},
            {"counter_value": 0, "unit": "energy_wh", "fault": 1},
            {"counter_value": 0, "unit": "energy_wh", "in_alarm": "true"},
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid values."""
        with pytest.raises(ValueError):
            MeteringValue.from_dict(data)


class TestDPTMeteringValue:
    """Test class for KNX DPTMeteringValue objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                MeteringValue(0, MeteringValueUnit.ENERGY_WH, -3),
                (0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                MeteringValue(2_147_483_647, MeteringValueUnit.ENERGY_WH, 3),
                (0x7F, 0xFF, 0xFF, 0xFF, 0x06, 0x00),
            ),
            (
                MeteringValue(-2_147_483_648, MeteringValueUnit.ENERGY_WH, 6),
                (0x80, 0x00, 0x00, 0x00, 0x81, 0x00),
            ),
            (
                MeteringValue(-1, MeteringValueUnit.VOLUME_M3, -3),
                (0xFF, 0xFF, 0xFF, 0xFF, 0x13, 0x00),
            ),
            (
                MeteringValue(
                    0x01020304,
                    MeteringValueUnit.DIMENSIONLESS_COUNTER,
                    out_of_service=True,
                    fault=True,
                    overridden=True,
                    in_alarm=True,
                    alarm_un_ack=True,
                ),
                (0x01, 0x02, 0x03, 0x04, 0xBA, 0x1F),
            ),
            # status bits
            (
                MeteringValue(0, MeteringValueUnit.HCA_UNITS, out_of_service=True),
                (0x00, 0x00, 0x00, 0x00, 0x6E, 0x01),
            ),
            (
                MeteringValue(1, MeteringValueUnit.HCA_UNITS, fault=True),
                (0x00, 0x00, 0x00, 0x01, 0x6E, 0x02),
            ),
            (
                MeteringValue(0, MeteringValueUnit.HCA_UNITS, overridden=True),
                (0x00, 0x00, 0x00, 0x00, 0x6E, 0x04),
            ),
            (
                MeteringValue(0, MeteringValueUnit.HCA_UNITS, in_alarm=True),
                (0x00, 0x00, 0x00, 0x00, 0x6E, 0x08),
            ),
            (
                MeteringValue(0, MeteringValueUnit.HCA_UNITS, alarm_un_ack=True),
                (0x00, 0x00, 0x00, 0x00, 0x6E, 0x10),
            ),
        ],
    )
    def test_round_trip(self, value: MeteringValue, raw: tuple[int, ...]) -> None:
        """Test DPTMeteringValue parsing and streaming."""
        knx_value = DPTMeteringValue.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTMeteringValue.from_knx(knx_value) == value

    @pytest.mark.parametrize(("code", "unit", "exponent"), _CODES)
    def test_val_inf_field(
        self, code: int, unit: MeteringValueUnit, exponent: int
    ) -> None:
        """Test every ValInfField code."""
        payload = DPTArray((0x00, 0x00, 0x00, 0x2A, code, 0x00))
        assert DPTMeteringValue.from_knx(payload) == MeteringValue(42, unit, exponent)
        assert DPTMeteringValue.to_knx(MeteringValue(42, unit, exponent)) == payload

    @pytest.mark.parametrize("code", _RESERVED_CODES)
    def test_from_knx_reserved_val_inf_field(self, code: int) -> None:
        """Test DPTMeteringValue parsing reserved ValInfField codes."""
        with pytest.raises(ConversionError):
            DPTMeteringValue.from_knx(DPTArray((0x00, 0x00, 0x00, 0x00, code, 0x00)))

    def test_from_knx_reserved_bits_ignored(self) -> None:
        """Test reserved bits of the Status/Command field are ignored."""
        assert DPTMeteringValue.from_knx(
            DPTArray((0x00, 0x00, 0x00, 0x00, 0x6E, 0xE0))
        ) == MeteringValue(0, MeteringValueUnit.HCA_UNITS)

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                {"counter_value": 1000, "unit": "power_w", "exponent": 5},
                (0x00, 0x00, 0x03, 0xE8, 0xA8, 0x00),
            ),
            (
                {
                    "counter_value": -5,
                    "unit": "mass_flow_kg_per_h",
                    "exponent": 4,
                    "fault": True,
                },
                (0xFF, 0xFF, 0xFF, 0xFB, 0x57, 0x02),
            ),
            (
                {"counter_value": 0, "unit": "dimensionless_counter"},
                (0x00, 0x00, 0x00, 0x00, 0xBA, 0x00),
            ),
        ],
    )
    def test_to_knx_from_dict(
        self, value: dict[str, Any], raw: tuple[int, ...]
    ) -> None:
        """Test DPTMeteringValue serializing from a dict."""
        assert DPTMeteringValue.to_knx(value) == DPTArray(raw)

    @pytest.mark.parametrize(
        "value",
        [
            MeteringValue(2_147_483_648, MeteringValueUnit.ENERGY_WH),
            MeteringValue(-2_147_483_649, MeteringValueUnit.ENERGY_WH),
            MeteringValue("a", MeteringValueUnit.ENERGY_WH),  # type: ignore[arg-type]
            MeteringValue(0, MeteringValueUnit.ENERGY_WH, -4),
            MeteringValue(0, MeteringValueUnit.ENERGY_WH, 7),
            MeteringValue(0, MeteringValueUnit.ENERGY_J, -1),
            MeteringValue(0, MeteringValueUnit.ENERGY_J, 10),
            MeteringValue(0, MeteringValueUnit.VOLUME_FLOW_M3_PER_S, -1),
            MeteringValue(0, MeteringValueUnit.HCA_UNITS, 1),
            MeteringValue(0, MeteringValueUnit.DIMENSIONLESS_COUNTER, -1),
            MeteringValue(0, "energy_wh"),  # type: ignore[arg-type]
            {"counter_value": 0, "unit": "energy_wh", "exponent": 7},
            {"counter_value": 0},
            None,
            1,
            (0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test DPTMeteringValue serializing invalid values."""
        with pytest.raises(ConversionError):
            DPTMeteringValue.to_knx(value)

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00, 0x00, 0x00, 0x00, 0x00)),
            DPTArray((0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)),
            DPTBinary(1),
        ],
    )
    def test_from_knx_invalid_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test DPTMeteringValue parsing invalid payloads."""
        with pytest.raises(CouldNotParseTelegram):
            DPTMeteringValue.from_knx(payload)

    @pytest.mark.parametrize("value_type", ["229.001", "metering_value"])
    def test_lookup(self, value_type: str) -> None:
        """Test transcoder lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder(value_type) is DPTMeteringValue
        assert DPTComplex.parse_transcoder(value_type) is DPTMeteringValue
        assert DPTBase.parse_transcoder({"main": 229, "sub": 1}) is DPTMeteringValue

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTMeteringValue."""
        assert DPTMeteringValue.get_dict_schema() == [
            {
                "name": "counter_value",
                "type": "integer",
                "required": True,
                "value_min": -2_147_483_648,
                "value_max": 2_147_483_647,
            },
            {
                "name": "unit",
                "type": "enum",
                "required": True,
                "options": [
                    "energy_wh",
                    "energy_j",
                    "volume_m3",
                    "mass_kg",
                    "power_w",
                    "power_j_per_h",
                    "volume_flow_m3_per_h",
                    "volume_flow_m3_per_min",
                    "volume_flow_m3_per_s",
                    "mass_flow_kg_per_h",
                    "hca_units",
                    "dimensionless_counter",
                ],
            },
            {
                "name": "exponent",
                "type": "integer",
                "required": False,
                "default": 0,
                "value_min": -9,
                "value_max": 9,
            },
            *(
                {"name": name, "type": "boolean", "required": False, "default": False}
                for name in _STATUS_BITS
            ),
        ]
