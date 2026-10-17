"""Unit test for KNX DPT 225.001 and 225.002 objects."""

from typing import Any

import pytest

from xknx.dpt import (
    DPTArray,
    DPTBase,
    DPTBinary,
    DPTScalingSpeed,
    DPTScalingStepTime,
    ScalingSpeed,
    ScalingStepTime,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram


class TestScalingSpeed:
    """Test ScalingSpeed and ScalingStepTime classes."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            ({"time_period": 4000, "percent": 100}, ScalingSpeed(4000, 100.0)),
            ({"time_period": "100", "percent": "0.4"}, ScalingSpeed(100, 0.4)),
            (
                {"time_period": 6_553_500, "percent": 75.3},
                ScalingSpeed(6_553_500, 75.3),
            ),
        ],
    )
    def test_dict_scaling_speed(
        self, data: dict[str, Any], value: ScalingSpeed
    ) -> None:
        """Test from_dict and as_dict methods of ScalingSpeed."""
        assert ScalingSpeed.from_dict(data) == value
        assert value.as_dict() == {
            "time_period": value.time_period,
            "percent": value.percent,
        }
        assert ScalingSpeed.from_dict(value.as_dict()) == value

    def test_dict_scaling_step_time(self) -> None:
        """Test from_dict and as_dict methods of ScalingStepTime."""
        value = ScalingStepTime.from_dict({"time_period": 15, "percent": 100})
        assert value == ScalingStepTime(15, 100.0)
        assert value.as_dict() == {"time_period": 15, "percent": 100.0}

    @pytest.mark.parametrize(
        "data",
        [
            {},
            {"time_period": 100},
            {"percent": 50},
            {"time_period": None, "percent": 50},
            {"time_period": "a", "percent": 50},
            {"time_period": 100, "percent": "a"},
            {"time_period": [], "percent": 50},
        ],
    )
    @pytest.mark.parametrize("data_class", [ScalingSpeed, ScalingStepTime])
    def test_dict_invalid(
        self,
        data: dict[str, Any],
        data_class: type[ScalingSpeed | ScalingStepTime],
    ) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            data_class.from_dict(data)


class TestDPTScalingSpeed:
    """Test class for KNX DPTScalingSpeed (225.001) objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            # spec examples
            (ScalingSpeed(4000, 100.0), (0x00, 0x28, 0xFF)),
            (ScalingSpeed(12_000, 75.3), (0x00, 0x78, 0xC0)),
            (ScalingSpeed(2000, 100.0), (0x00, 0x14, 0xFF)),
            # limits
            (ScalingSpeed(100, 0.4), (0x00, 0x01, 0x01)),
            (ScalingSpeed(6_553_500, 100.0), (0xFF, 0xFF, 0xFF)),
            (ScalingSpeed(25_600, 50.2), (0x01, 0x00, 0x80)),
        ],
    )
    def test_value(self, value: ScalingSpeed, raw: tuple[int, ...]) -> None:
        """Test DPTScalingSpeed parsing and streaming."""
        knx_value = DPTScalingSpeed.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTScalingSpeed.from_knx(knx_value) == value

    def test_spec_example_percent(self) -> None:
        """75 % of the spec example encodes like DPT_Scaling (5.001)."""
        assert DPTScalingSpeed.to_knx(ScalingSpeed(12_000, 75)) == DPTArray(
            (0x00, 0x78, 0xBF)
        )

    @pytest.mark.parametrize("raw_percent", range(1, 256))
    def test_percent_round_trip(self, raw_percent: int) -> None:
        """Test every percent raw value survives a round trip."""
        raw = DPTArray((0x00, 0x01, raw_percent))
        assert DPTScalingSpeed.to_knx(DPTScalingSpeed.from_knx(raw)) == raw

    def test_to_knx_from_dict(self) -> None:
        """Test DPTScalingSpeed serializing from a dict."""
        assert DPTScalingSpeed.to_knx(
            {"time_period": 4000, "percent": 100}
        ) == DPTArray((0x00, 0x28, 0xFF))

    @pytest.mark.parametrize(
        "value",
        [
            ScalingSpeed(99, 50),
            ScalingSpeed(0, 50),
            ScalingSpeed(6_553_501, 50),
            ScalingSpeed(1000, 0.3),
            ScalingSpeed(1000, 0),
            ScalingSpeed(1000, 100.1),
            ScalingSpeed(1000, -1),
            ScalingSpeed("a", 50),  # type: ignore[arg-type]
            ScalingSpeed(1000, "a"),  # type: ignore[arg-type]
            {"time_period": 1000},
            {"time_period": 1000, "percent": "a"},
            None,
            1,
            (0x00, 0x28, 0xFF),
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test DPTScalingSpeed serializing with invalid values."""
        with pytest.raises(ConversionError):
            DPTScalingSpeed.to_knx(value)

    @pytest.mark.parametrize(
        "raw",
        [
            (0x00, 0x00, 0xFF),  # time period 0
            (0x00, 0x28, 0x00),  # percent 0
        ],
    )
    def test_from_knx_out_of_range(self, raw: tuple[int, ...]) -> None:
        """Test DPTScalingSpeed parsing of out of range values."""
        with pytest.raises(ConversionError):
            DPTScalingSpeed.from_knx(DPTArray(raw))

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00, 0x28)),
            DPTArray((0x00, 0x28, 0xFF, 0x00)),
            DPTBinary(1),
        ],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test DPTScalingSpeed parsing with wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTScalingSpeed.from_knx(payload)

    def test_lookup(self) -> None:
        """Test DPTScalingSpeed lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder("225.001") is DPTScalingSpeed
        assert DPTBase.parse_transcoder("scaling_speed") is DPTScalingSpeed

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema of DPTScalingSpeed."""
        assert DPTScalingSpeed.get_dict_schema() == [
            {
                "name": "time_period",
                "type": "integer",
                "required": True,
                "value_min": 100,
                "value_max": 6_553_500,
                "resolution": 100,
            },
            {
                "name": "percent",
                "type": "float",
                "required": True,
                "value_min": 0.4,
                "value_max": 100.0,
                "resolution": 0.4,
            },
        ]


class TestDPTScalingStepTime:
    """Test class for KNX DPTScalingStepTime (225.002) objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            # spec examples
            (ScalingStepTime(15, 100.0), (0x00, 0x0F, 0xFF)),
            (ScalingStepTime(62, 75.3), (0x00, 0x3E, 0xC0)),
            (ScalingStepTime(31, 100.0), (0x00, 0x1F, 0xFF)),
            # limits
            (ScalingStepTime(1, 0.4), (0x00, 0x01, 0x01)),
            (ScalingStepTime(65_535, 100.0), (0xFF, 0xFF, 0xFF)),
            (ScalingStepTime(256, 50.2), (0x01, 0x00, 0x80)),
        ],
    )
    def test_value(self, value: ScalingStepTime, raw: tuple[int, ...]) -> None:
        """Test DPTScalingStepTime parsing and streaming."""
        knx_value = DPTScalingStepTime.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTScalingStepTime.from_knx(knx_value) == value

    def test_to_knx_from_dict(self) -> None:
        """Test DPTScalingStepTime serializing from a dict."""
        assert DPTScalingStepTime.to_knx(
            {"time_period": 15, "percent": 100}
        ) == DPTArray((0x00, 0x0F, 0xFF))

    @pytest.mark.parametrize(
        "value",
        [
            ScalingStepTime(0, 50),
            ScalingStepTime(65_536, 50),
            ScalingStepTime(-1, 50),
            ScalingStepTime(15, 0.3),
            ScalingStepTime(15, 100.1),
            ScalingStepTime(15, "a"),  # type: ignore[arg-type]
            {"percent": 50},
            None,
            (0x00, 0x0F, 0xFF),
        ],
    )
    def test_to_knx_invalid(self, value: Any) -> None:
        """Test DPTScalingStepTime serializing with invalid values."""
        with pytest.raises(ConversionError):
            DPTScalingStepTime.to_knx(value)

    @pytest.mark.parametrize(
        "raw",
        [
            (0x00, 0x00, 0xFF),  # time period 0
            (0x00, 0x0F, 0x00),  # percent 0
        ],
    )
    def test_from_knx_out_of_range(self, raw: tuple[int, ...]) -> None:
        """Test DPTScalingStepTime parsing of out of range values."""
        with pytest.raises(ConversionError):
            DPTScalingStepTime.from_knx(DPTArray(raw))

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00, 0x0F)),
            DPTArray((0x00, 0x0F, 0xFF, 0x00)),
            DPTBinary(1),
        ],
    )
    def test_from_knx_wrong_payload(self, payload: DPTArray | DPTBinary) -> None:
        """Test DPTScalingStepTime parsing with wrong payload."""
        with pytest.raises(CouldNotParseTelegram):
            DPTScalingStepTime.from_knx(payload)

    def test_lookup(self) -> None:
        """Test DPTScalingStepTime lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder("225.002") is DPTScalingStepTime
        assert DPTBase.parse_transcoder("scaling_step_time") is DPTScalingStepTime

    def test_get_dict_schema(self) -> None:
        """Test get_dict_schema of DPTScalingStepTime."""
        assert DPTScalingStepTime.get_dict_schema() == [
            {
                "name": "time_period",
                "type": "integer",
                "required": True,
                "value_min": 1,
                "value_max": 65_535,
            },
            {
                "name": "percent",
                "type": "float",
                "required": True,
                "value_min": 0.4,
                "value_max": 100.0,
                "resolution": 0.4,
            },
        ]
