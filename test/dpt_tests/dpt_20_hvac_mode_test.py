"""Unit test for KNX DPT HVAC Operation modes."""

from typing import Any

import pytest

from xknx.dpt import (
    DPTArray,
    DPTBase,
    DPTBinary,
    DPTChangeoverMode,
    DPTEnableHCStage,
    DPTHVACContrMode,
    DPTHVACMode,
    DPTHVACStatus,
)
from xknx.dpt.dpt_20 import (
    ChangeoverMode,
    EnableHCStage,
    HeatCool,
    HVACControllerMode,
    HVACOperationMode,
    HVACStatus,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTHVACMode:
    """Test class for KNX DPT HVAC Operation modes."""

    def test_mode_to_knx(self) -> None:
        """Test parsing DPTHVACMode to KNX."""
        assert DPTHVACMode.to_knx(HVACOperationMode.AUTO) == DPTArray((0x00,))
        assert DPTHVACMode.to_knx(HVACOperationMode.COMFORT) == DPTArray((0x01,))
        assert DPTHVACMode.to_knx(HVACOperationMode.STANDBY) == DPTArray((0x02,))
        assert DPTHVACMode.to_knx(HVACOperationMode.ECONOMY) == DPTArray((0x03,))
        assert DPTHVACMode.to_knx(HVACOperationMode.BUILDING_PROTECTION) == DPTArray(
            (0x04,)
        )

    def test_mode_to_knx_by_string(self) -> None:
        """Test parsing DPTHVACMode string values to KNX."""
        assert DPTHVACMode.to_knx("auto") == DPTArray((0x00,))
        assert DPTHVACMode.to_knx("Comfort") == DPTArray((0x01,))
        assert DPTHVACMode.to_knx("standby") == DPTArray((0x02,))
        assert DPTHVACMode.to_knx("ECONOMY") == DPTArray((0x03,))
        assert DPTHVACMode.to_knx("Building_Protection") == DPTArray((0x04,))

    def test_mode_to_knx_wrong_value(self) -> None:
        """Test serializing DPTHVACMode to KNX with wrong value."""
        with pytest.raises(ConversionError):
            DPTHVACMode.to_knx(5)

    def test_mode_from_knx(self) -> None:
        """Test parsing DPTHVACMode from KNX."""
        assert DPTHVACMode.from_knx(DPTArray((0x00,))) == HVACOperationMode.AUTO
        assert DPTHVACMode.from_knx(DPTArray((0x01,))) == HVACOperationMode.COMFORT
        assert DPTHVACMode.from_knx(DPTArray((0x02,))) == HVACOperationMode.STANDBY
        assert DPTHVACMode.from_knx(DPTArray((0x03,))) == HVACOperationMode.ECONOMY
        assert (
            DPTHVACMode.from_knx(DPTArray((0x04,)))
            == HVACOperationMode.BUILDING_PROTECTION
        )

    def test_mode_from_knx_wrong_value(self) -> None:
        """Test parsing of DPTHVACMode with wrong value)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTHVACMode.from_knx(DPTArray((1, 2)))
        with pytest.raises(ConversionError):
            DPTHVACMode.from_knx(DPTArray((0x05,)))


class TestDPTHVACControllerMode:
    """Test class for KNX DPT HVAC Controller modes."""

    def test_mode_to_knx(self) -> None:
        """Test parsing DPTHVACContrMode to KNX."""
        assert DPTHVACContrMode.to_knx(HVACControllerMode.AUTO) == DPTArray((0x00,))
        assert DPTHVACContrMode.to_knx(HVACControllerMode.HEAT) == DPTArray((0x01,))
        assert DPTHVACContrMode.to_knx(HVACControllerMode.COOL) == DPTArray((0x03,))
        assert DPTHVACContrMode.to_knx(HVACControllerMode.OFF) == DPTArray((0x06,))
        assert DPTHVACContrMode.to_knx(HVACControllerMode.DEHUMIDIFICATION) == DPTArray(
            (0x0E,)
        )

    def test_mode_to_knx_by_string(self) -> None:
        """Test parsing DPTHVACMode string values to KNX."""
        assert DPTHVACContrMode.to_knx("morning_warmup") == DPTArray((0x02,))
        assert DPTHVACContrMode.to_knx("NIGHT_PURGE") == DPTArray((0x04,))
        assert DPTHVACContrMode.to_knx("precool") == DPTArray((0x05,))
        assert DPTHVACContrMode.to_knx("Test") == DPTArray((0x07,))
        assert DPTHVACContrMode.to_knx("NODEM") == DPTArray((0x14,))

    def test_mode_to_knx_wrong_value(self) -> None:
        """Test serializing DPTHVACMode to KNX with wrong value."""
        with pytest.raises(ConversionError):
            DPTHVACContrMode.to_knx(18)
        with pytest.raises(ConversionError):
            DPTHVACContrMode.to_knx(19)
        with pytest.raises(ConversionError):
            DPTHVACContrMode.to_knx(21)

    @pytest.mark.parametrize(
        ("raw", "value"),
        [
            (0x00, HVACControllerMode.AUTO),
            (0x08, HVACControllerMode.EMERGENCY_HEAT),
            (0x09, HVACControllerMode.FAN_ONLY),
            (0x0A, HVACControllerMode.FREE_COOL),
            (0x0B, HVACControllerMode.ICE),
        ],
    )
    def test_mode_from_knx(self, raw: int, value: HVACControllerMode) -> None:
        """Test parsing DPTHVACMode from KNX."""
        assert DPTHVACContrMode.from_knx(DPTArray((raw,))) is value

    def test_mode_from_knx_wrong_value(self) -> None:
        """Test parsing of DPTHVACMode with wrong value)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTHVACContrMode.from_knx(DPTArray((1, 2)))
        with pytest.raises(ConversionError):
            DPTHVACContrMode.from_knx(DPTArray((18,)))


class TestDPTChangeoverMode:
    """Test class for KNX DPT 20.107 changeover mode."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (ChangeoverMode.AUTO, 0x00),
            (ChangeoverMode.COOLING_ONLY, 0x01),
            (ChangeoverMode.HEATING_ONLY, 0x02),
        ],
    )
    def test_transcoder(self, value: ChangeoverMode, raw: int) -> None:
        """Test parsing and streaming of DPTChangeoverMode."""
        assert DPTChangeoverMode.to_knx(value) == DPTArray((raw,))
        assert DPTChangeoverMode.from_knx(DPTArray((raw,))) is value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            ("auto", 0x00),
            ("Cooling_Only", 0x01),
            ("HEATING_ONLY", 0x02),
            (0, 0x00),
            (2, 0x02),
        ],
    )
    def test_to_knx_by_name_or_value(self, value: str | int, raw: int) -> None:
        """Test serializing DPTChangeoverMode from a name or a raw value."""
        assert DPTChangeoverMode.to_knx(value) == DPTArray((raw,))

    @pytest.mark.parametrize("value", [3, 255, "heating", "", None, 1.5])
    def test_to_knx_wrong_value(self, value: Any) -> None:
        """Test serializing DPTChangeoverMode with a wrong value."""
        with pytest.raises(ConversionError):
            DPTChangeoverMode.to_knx(value)

    def test_from_knx_wrong_value(self) -> None:
        """Test parsing DPTChangeoverMode with a reserved value or wrong payload."""
        with pytest.raises(ConversionError):
            DPTChangeoverMode.from_knx(DPTArray((0x03,)))
        with pytest.raises(ConversionError):
            DPTChangeoverMode.from_knx(DPTArray((0xFF,)))
        with pytest.raises(CouldNotParseTelegram):
            DPTChangeoverMode.from_knx(DPTArray((0x00, 0x00)))
        with pytest.raises(CouldNotParseTelegram):
            DPTChangeoverMode.from_knx(DPTBinary(1))

    def test_valid_values(self) -> None:
        """Test the valid values of DPTChangeoverMode."""
        assert DPTChangeoverMode.get_valid_values() == [
            ChangeoverMode.AUTO,
            ChangeoverMode.COOLING_ONLY,
            ChangeoverMode.HEATING_ONLY,
        ]

    def test_lookup(self) -> None:
        """Test lookup of DPTChangeoverMode."""
        assert DPTBase.parse_transcoder("20.107") is DPTChangeoverMode
        assert DPTBase.parse_transcoder("changeover_mode") is DPTChangeoverMode


class TestDPTEnableHCStage:
    """Test class for KNX DPT 20.116 enable heating/cooling stage."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (EnableHCStage.DISABLED, 0x00),
            (EnableHCStage.STAGE_A, 0x01),
            (EnableHCStage.STAGE_B, 0x02),
            (EnableHCStage.BOTH_STAGES, 0x03),
        ],
    )
    def test_transcoder(self, value: EnableHCStage, raw: int) -> None:
        """Test parsing and streaming of DPTEnableHCStage."""
        assert DPTEnableHCStage.to_knx(value) == DPTArray((raw,))
        assert DPTEnableHCStage.from_knx(DPTArray((raw,))) is value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            ("disabled", 0x00),
            ("Stage_A", 0x01),
            ("STAGE_B", 0x02),
            ("both_stages", 0x03),
            (0, 0x00),
            (3, 0x03),
        ],
    )
    def test_to_knx_by_name_or_value(self, value: str | int, raw: int) -> None:
        """Test serializing DPTEnableHCStage from a name or a raw value."""
        assert DPTEnableHCStage.to_knx(value) == DPTArray((raw,))

    @pytest.mark.parametrize("value", [4, 255, "stage_c", "", None, 1.5])
    def test_to_knx_wrong_value(self, value: Any) -> None:
        """Test serializing DPTEnableHCStage with a wrong value."""
        with pytest.raises(ConversionError):
            DPTEnableHCStage.to_knx(value)

    def test_from_knx_wrong_value(self) -> None:
        """Test parsing DPTEnableHCStage with a reserved value or wrong payload."""
        with pytest.raises(ConversionError):
            DPTEnableHCStage.from_knx(DPTArray((0x04,)))
        with pytest.raises(ConversionError):
            DPTEnableHCStage.from_knx(DPTArray((0xFF,)))
        with pytest.raises(CouldNotParseTelegram):
            DPTEnableHCStage.from_knx(DPTArray((0x00, 0x00)))
        with pytest.raises(CouldNotParseTelegram):
            DPTEnableHCStage.from_knx(DPTBinary(1))

    def test_valid_values(self) -> None:
        """Test the valid values of DPTEnableHCStage."""
        assert DPTEnableHCStage.get_valid_values() == [
            EnableHCStage.DISABLED,
            EnableHCStage.STAGE_A,
            EnableHCStage.STAGE_B,
            EnableHCStage.BOTH_STAGES,
        ]

    def test_lookup(self) -> None:
        """Test lookup of DPTEnableHCStage."""
        assert DPTBase.parse_transcoder("20.116") is DPTEnableHCStage
        assert DPTBase.parse_transcoder("enable_hc_stage") is DPTEnableHCStage


class TestHVACStatus:
    """Test HVACStatus class."""

    @pytest.mark.parametrize(
        ("data", "dict_value"),
        [
            (
                HVACStatus(
                    mode=HVACOperationMode.COMFORT,
                    dew_point=False,
                    heat_cool=HeatCool.HEAT,
                    inactive=False,
                    frost_alarm=False,
                ),
                {
                    "mode": "comfort",
                    "dew_point": False,
                    "heat_cool": "heat",
                    "inactive": False,
                    "frost_alarm": False,
                },
            ),
            (
                HVACStatus(
                    mode=HVACOperationMode.STANDBY,
                    dew_point=False,
                    heat_cool=HeatCool.COOL,
                    inactive=True,
                    frost_alarm=False,
                ),
                {
                    "mode": "standby",
                    "dew_point": False,
                    "heat_cool": "cool",
                    "inactive": True,
                    "frost_alarm": False,
                },
            ),
        ],
    )
    def test_dict(self, data: HVACStatus, dict_value: dict[str, Any]) -> None:
        """Test from_dict and as_dict methods."""
        assert HVACStatus.from_dict(dict_value) == data
        assert data.as_dict() == dict_value

    @pytest.mark.parametrize(
        "data",
        [
            {
                "mode": 1,  # invalid
                "dew_point": False,
                "heat_cool": "heat",
                "inactive": False,
                "frost_alarm": False,
            },
            {
                "mode": "comfort",
                "dew_point": False,
                "heat_cool": "invalid",  # invalid
                "inactive": False,
                "frost_alarm": False,
            },
            {
                "mode": "comfort",
                "dew_point": False,
                "heat_cool": "nodem",  # invalid for HVACStatus
                "inactive": False,
                "frost_alarm": False,
            },
            {
                "mode": "comfort",
                "dew_point": 20,  # invalid
                "heat_cool": "heat",
                "inactive": False,
                "frost_alarm": False,
            },
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            HVACStatus.from_dict(data)


class TestDPTHVACStatus:
    """Test class for KNX DPTHVACStatus objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                HVACStatus(
                    mode=HVACOperationMode.COMFORT,
                    dew_point=False,
                    heat_cool=HeatCool.HEAT,
                    inactive=False,
                    frost_alarm=False,
                ),
                (0x21,),
            ),
            (
                HVACStatus(
                    mode=HVACOperationMode.COMFORT,
                    dew_point=False,
                    heat_cool=HeatCool.COOL,
                    inactive=False,
                    frost_alarm=False,
                ),
                (0x01,),
            ),
            (
                HVACStatus(
                    mode=HVACOperationMode.ECONOMY,
                    dew_point=True,
                    heat_cool=HeatCool.COOL,
                    inactive=False,
                    frost_alarm=True,
                ),
                (0x94,),
            ),
        ],
    )
    def test_dpt_encoding_decoding(self, value: HVACStatus, raw: tuple[int]) -> None:
        """Test DPTHVACStatus parsing and streaming."""
        knx_value = DPTHVACStatus.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTHVACStatus.from_knx(knx_value) == value

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                {
                    "mode": "comfort",
                    "dew_point": False,
                    "heat_cool": "heat",
                    "inactive": False,
                    "frost_alarm": False,
                },
                (0x21,),
            ),
            (
                {
                    "mode": "standby",
                    "dew_point": False,
                    "heat_cool": "cool",
                    "inactive": True,
                    "frost_alarm": False,
                },
                (0x42,),
            ),
        ],
    )
    def test_dpt_to_knx_from_dict(self, value: dict[str, Any], raw: tuple[int]) -> None:
        """Test DPTHVACStatus parsing from a dict."""
        knx_value = DPTHVACStatus.to_knx(value)
        assert knx_value == DPTArray(raw)

    @pytest.mark.parametrize(
        "value",
        [
            {"mode": "comfort", "dew_point": False, "heat_cool": "heat"},
            1,
            "cool",
        ],
    )
    def test_dpt_wrong_value_to_knx(self, value: Any) -> None:
        """Test DPTHVACStatus parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTHVACStatus.to_knx(value)

    def test_dpt_wrong_value_from_knx(self) -> None:
        """Test DPTHVACStatus parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPTHVACStatus.from_knx(DPTArray((0xFF, 0x4E)))

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema returns correct schema for DPTHVACStatus."""
        assert DPTHVACStatus.get_dict_schema() == [
            {
                "name": "mode",
                "type": "enum",
                "required": True,
                "options": [
                    "auto",
                    "comfort",
                    "standby",
                    "economy",
                    "building_protection",
                ],
            },
            {"name": "dew_point", "type": "boolean", "required": True},
            {
                "name": "heat_cool",
                "type": "enum",
                "required": True,
                "options": ["cool", "heat"],
            },
            {"name": "inactive", "type": "boolean", "required": True},
            {"name": "frost_alarm", "type": "boolean", "required": True},
        ]
