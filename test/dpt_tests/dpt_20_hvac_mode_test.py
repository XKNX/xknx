"""Unit test for KNX DPT HVAC Operation modes."""

import pytest

from xknx.dpt import DPTArray, DPTHVACContrMode, DPTHVACMode, DPTHVACStatus
from xknx.dpt.dpt_20 import HeatCool, HVACControllerMode, HVACOperationMode, HVACStatus
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestDPTHVACMode:
    """Test class for KNX DPT HVAC Operation modes."""

    def test_mode_to_knx(self):
        """Test parsing DPTHVACMode to KNX."""
        assert DPTHVACMode.to_knx(HVACOperationMode.AUTO) == DPTArray((0x00,))
        assert DPTHVACMode.to_knx(HVACOperationMode.COMFORT) == DPTArray((0x01,))
        assert DPTHVACMode.to_knx(HVACOperationMode.STANDBY) == DPTArray((0x02,))
        assert DPTHVACMode.to_knx(HVACOperationMode.ECONOMY) == DPTArray((0x03,))
        assert DPTHVACMode.to_knx(HVACOperationMode.BUILDING_PROTECTION) == DPTArray(
            (0x04,)
        )

    def test_mode_to_knx_by_string(self):
        """Test parsing DPTHVACMode string values to KNX."""
        assert DPTHVACMode.to_knx("auto") == DPTArray((0x00,))
        assert DPTHVACMode.to_knx("Comfort") == DPTArray((0x01,))
        assert DPTHVACMode.to_knx("standby") == DPTArray((0x02,))
        assert DPTHVACMode.to_knx("ECONOMY") == DPTArray((0x03,))
        assert DPTHVACMode.to_knx("Building_Protection") == DPTArray((0x04,))

    def test_mode_to_knx_wrong_value(self):
        """Test serializing DPTHVACMode to KNX with wrong value."""
        with pytest.raises(ConversionError):
            DPTHVACMode.to_knx(5)

    def test_mode_from_knx(self):
        """Test parsing DPTHVACMode from KNX."""
        assert DPTHVACMode.from_knx(DPTArray((0x00,))) == HVACOperationMode.AUTO
        assert DPTHVACMode.from_knx(DPTArray((0x01,))) == HVACOperationMode.COMFORT
        assert DPTHVACMode.from_knx(DPTArray((0x02,))) == HVACOperationMode.STANDBY
        assert DPTHVACMode.from_knx(DPTArray((0x03,))) == HVACOperationMode.ECONOMY
        assert (
            DPTHVACMode.from_knx(DPTArray((0x04,)))
            == HVACOperationMode.BUILDING_PROTECTION
        )

    def test_mode_from_knx_wrong_value(self):
        """Test parsing of DPTHVACMode with wrong value)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTHVACMode.from_knx(DPTArray((1, 2)))
        with pytest.raises(ConversionError):
            DPTHVACMode.from_knx(DPTArray((0x05,)))


class TestDPTHVACControllerMode:
    """Test class for KNX DPT HVAC Controller modes."""

    def test_mode_to_knx(self):
        """Test parsing DPTHVACContrMode to KNX."""
        assert DPTHVACContrMode.to_knx(HVACControllerMode.AUTO) == DPTArray((0x00,))
        assert DPTHVACContrMode.to_knx(HVACControllerMode.HEAT) == DPTArray((0x01,))
        assert DPTHVACContrMode.to_knx(HVACControllerMode.COOL) == DPTArray((0x03,))
        assert DPTHVACContrMode.to_knx(HVACControllerMode.OFF) == DPTArray((0x06,))
        assert DPTHVACContrMode.to_knx(HVACControllerMode.DEHUMIDIFICATION) == DPTArray(
            (0x0E,)
        )

    def test_mode_to_knx_by_string(self):
        """Test parsing DPTHVACMode string values to KNX."""
        assert DPTHVACContrMode.to_knx("morning_warmup") == DPTArray((0x02,))
        assert DPTHVACContrMode.to_knx("NIGHT_PURGE") == DPTArray((0x04,))
        assert DPTHVACContrMode.to_knx("precool") == DPTArray((0x05,))
        assert DPTHVACContrMode.to_knx("Test") == DPTArray((0x07,))
        assert DPTHVACContrMode.to_knx("NODEM") == DPTArray((0x14,))

    def test_mode_to_knx_wrong_value(self):
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
    def test_mode_from_knx(self, raw, value):
        """Test parsing DPTHVACMode from KNX."""
        assert DPTHVACContrMode.from_knx(DPTArray((raw,))) is value

    def test_mode_from_knx_wrong_value(self):
        """Test parsing of DPTHVACMode with wrong value)."""
        with pytest.raises(CouldNotParseTelegram):
            DPTHVACContrMode.from_knx(DPTArray((1, 2)))
        with pytest.raises(ConversionError):
            DPTHVACContrMode.from_knx(DPTArray((18,)))


class TestHVACStatus:
    """Test HVACStatus class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {
                    "mode": "comfort",
                    "dew_point": False,
                    "heat_cool": "heat",
                    "inactive": False,
                    "frost_alarm": False,
                },
                HVACStatus(
                    mode=HVACOperationMode.COMFORT,
                    dew_point=False,
                    heat_cool=HeatCool.HEAT,
                    inactive=False,
                    frost_alarm=False,
                ),
            ),
            (
                {
                    "mode": "standby",
                    "dew_point": False,
                    "heat_cool": "cool",
                    "inactive": True,
                    "frost_alarm": False,
                },
                HVACStatus(
                    mode=HVACOperationMode.STANDBY,
                    dew_point=False,
                    heat_cool=HeatCool.COOL,
                    inactive=True,
                    frost_alarm=False,
                ),
            ),
        ],
    )
    def test_dict(self, data, value):
        """Test from_dict and as_dict methods."""
        test_value = HVACStatus.from_dict(data)
        assert test_value == value
        assert value.as_dict() == data

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
    def test_dict_invalid(self, data):
        """Test from_dict and as_dict methods."""
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
                (0b10000100,),
            ),
            (
                HVACStatus(
                    mode=HVACOperationMode.COMFORT,
                    dew_point=False,
                    heat_cool=HeatCool.COOL,
                    inactive=False,
                    frost_alarm=False,
                ),
                (0b10000000,),
            ),  # min values
            (
                HVACStatus(
                    mode=HVACOperationMode.ECONOMY,
                    dew_point=True,
                    heat_cool=HeatCool.COOL,
                    inactive=False,
                    frost_alarm=True,
                ),
                (0b00101001,),
            ),
        ],
    )
    def test_dpt_encoding_decoding(self, value, raw):
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
                (0b10000100,),
            ),
            (
                {
                    "mode": "standby",
                    "dew_point": False,
                    "heat_cool": "cool",
                    "inactive": True,
                    "frost_alarm": False,
                },
                (0b01000010,),
            ),
        ],
    )
    def test_dpt_to_knx_from_dict(self, value, raw):
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
    def test_dpt_wrong_value_to_knx(self, value):
        """Test DPTHVACStatus parsing with wrong value."""
        with pytest.raises(ConversionError):
            DPTHVACStatus.to_knx(value)

    def test_dpt_wrong_value_from_knx(self):
        """Test DPTHVACStatus parsing with wrong value."""
        with pytest.raises(CouldNotParseTelegram):
            DPTHVACStatus.from_knx(DPTArray((0xFF, 0x4E)))
