"""Unit test for KNX scaling speed DPT."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTScalingSpeed, ScalingSpeed
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestScalingSpeed:
    """Test ScalingSpeed class and DPTScalingSpeed (225.001)."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                ScalingSpeed(time_period=0.1, percent=0),
                (0x00, 0x01, 0x00),
            ),
            (
                ScalingSpeed(time_period=6553.5, percent=100),
                (0xFF, 0xFF, 0xFF),
            ),
            (
                ScalingSpeed(time_period=6.0, percent=100),
                (0x00, 0x3C, 0xFF),
            ),
            (
                ScalingSpeed(time_period=1.0, percent=50),
                (0x00, 0x0A, 0x80),
            ),
        ],
    )
    def test_value(self, value: ScalingSpeed, raw: tuple[int, ...]) -> None:
        """Test DPTScalingSpeed parsing and streaming."""
        knx_value = DPTScalingSpeed.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTScalingSpeed.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test DPTScalingSpeed parsing from a dict."""
        knx_value = DPTScalingSpeed.to_knx({"time_period": 1.0, "percent": 50})
        assert knx_value == DPTArray((0x00, 0x0A, 0x80))

    @pytest.mark.parametrize(
        ("time_period", "percent"),
        [
            (0.0, 0),  # time_period below minimum
            (6553.6, 0),  # time_period above maximum
            (1.0, -1),  # percent below minimum
            (1.0, 101),  # percent above maximum
        ],
    )
    def test_to_knx_limits(self, time_period: float, percent: float) -> None:
        """Test serializing DPTScalingSpeed with out-of-range values."""
        value = ScalingSpeed(time_period=time_period, percent=percent)
        with pytest.raises(ConversionError):
            DPTScalingSpeed.to_knx(value)

    def test_wrong_value_from_knx(self) -> None:
        """Test DPTScalingSpeed parsing with wrong payload length."""
        with pytest.raises(CouldNotParseTelegram):
            DPTScalingSpeed.from_knx(DPTArray((0x00, 0x00)))

    def test_from_dict_missing_key(self) -> None:
        """Test that both time_period and percent are required when parsing from a dict."""
        with pytest.raises(ConversionError):
            DPTScalingSpeed.to_knx({"time_period": 1.0})
        with pytest.raises(ConversionError):
            DPTScalingSpeed.to_knx({"percent": 50})

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema - both fields are required."""
        assert DPTScalingSpeed.get_dict_schema() == [
            {
                "name": "time_period",
                "type": "float",
                "required": True,
                "value_min": 0.1,
                "value_max": 6553.5,
                "resolution": 0.1,
            },
            {
                "name": "percent",
                "type": "float",
                "required": True,
                "value_min": 0,
                "value_max": 100,
            },
        ]

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {"time_period": 1.0, "percent": 50},
                ScalingSpeed(time_period=1.0, percent=50),
            ),
            (
                {"time_period": "1.0", "percent": "50"},
                ScalingSpeed(time_period=1.0, percent=50.0),
            ),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: ScalingSpeed) -> None:
        """Test from_dict and as_dict methods."""
        assert ScalingSpeed.from_dict(data) == value
        assert value.as_dict() == {
            "time_period": value.time_period,
            "percent": value.percent,
        }

    @pytest.mark.parametrize(
        "data",
        [
            {"time_period": "a", "percent": 50},  # invalid time_period
            {"time_period": 1.0, "percent": "a"},  # invalid percent
            {"time_period": 1.0},  # missing required percent
            {"percent": 50},  # missing required time_period
            {},  # missing both
        ],
    )
    def test_dict_invalid(self, data: dict[str, Any]) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            ScalingSpeed.from_dict(data)
