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
            ({"time_period": 4000, "percent": 100}, ScalingSpeed(4000, 100)),
            ({"time_period": "100", "percent": "1"}, ScalingSpeed(100, 1)),
            ({"time_period": 6_553_500, "percent": 75}, ScalingSpeed(6_553_500, 75)),
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
        assert value == ScalingStepTime(15, 100)
        assert value.as_dict() == {"time_period": 15, "percent": 100}

    @pytest.mark.parametrize(
        "data",
        [
            # both fields are required - there is no invalid marker in the telegram
            {},
            {"time_period": 100},
            {"percent": 50},
            {"time_period": None, "percent": 50},
            {"time_period": "a", "percent": 50},
            {"time_period": 100, "percent": "a"},
            {"time_period": 100, "percent": "0.4"},
            {"time_period": [], "percent": 50},
            # not a mapping
            1,
            None,
            "time_period",
            [("time_period", 100), ("percent", 50)],
        ],
    )
    @pytest.mark.parametrize("data_class", [ScalingSpeed, ScalingStepTime])
    def test_dict_invalid(
        self,
        data: Any,
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
            (ScalingSpeed(4000, 100), (0x00, 0x28, 0xFF)),
            (ScalingSpeed(2000, 100), (0x00, 0x14, 0xFF)),
            # limits
            (ScalingSpeed(100, 1), (0x00, 0x01, 0x03)),
            (ScalingSpeed(6_553_500, 100), (0xFF, 0xFF, 0xFF)),
            (ScalingSpeed(25_600, 50), (0x01, 0x00, 0x80)),
        ],
    )
    def test_value(self, value: ScalingSpeed, raw: tuple[int, ...]) -> None:
        """Test DPTScalingSpeed parsing and streaming."""
        knx_value = DPTScalingSpeed.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTScalingSpeed.from_knx(knx_value) == value

    def test_spec_example_percent(self) -> None:
        """75 % of the spec example (C0h) is encoded like DPT 5.001 (BFh)."""
        assert DPTScalingSpeed.from_knx(DPTArray((0x00, 0x78, 0xC0))) == ScalingSpeed(
            12_000, 75
        )
        assert DPTScalingSpeed.to_knx(ScalingSpeed(12_000, 75)) == DPTArray(
            (0x00, 0x78, 0xBF)
        )

    @pytest.mark.parametrize(
        ("time_period", "raw_time_period"),
        [
            (100, 0x01),
            (149, 0x01),
            (151, 0x02),
            (199, 0x02),
            (200, 0x02),
            (249, 0x02),
            (6_553_549, 0xFFFF),
        ],
    )
    def test_time_period_rounding(self, time_period: int, raw_time_period: int) -> None:
        """Test the time period is rounded to 100 ms like DPT 7.004."""
        assert DPTScalingSpeed.to_knx(ScalingSpeed(time_period, 100)) == DPTArray(
            (raw_time_period >> 8, raw_time_period & 0xFF, 0xFF)
        )

    @pytest.mark.parametrize("percent", range(1, 101))
    def test_percent_round_trip(self, percent: int) -> None:
        """Test every percent value survives a round trip."""
        value = ScalingSpeed(100, percent)
        assert DPTScalingSpeed.from_knx(DPTScalingSpeed.to_knx(value)) == value

    def test_to_knx_from_dict(self) -> None:
        """Test DPTScalingSpeed serializing from a dict."""
        assert DPTScalingSpeed.to_knx(
            {"time_period": 4000, "percent": 100}
        ) == DPTArray((0x00, 0x28, 0xFF))

    @pytest.mark.parametrize(
        "value",
        [
            ScalingSpeed(49, 50),
            ScalingSpeed(0, 50),
            ScalingSpeed(-100, 50),
            ScalingSpeed(6_553_551, 50),
            ScalingSpeed(6_553_600, 50),
            ScalingSpeed(1000, 0),
            ScalingSpeed(1000, 0.1),  # type: ignore[arg-type]
            ScalingSpeed(1000, 101),
            ScalingSpeed(1000, -1),
            ScalingSpeed("a", 50),  # type: ignore[arg-type]
            ScalingSpeed(1000, "a"),  # type: ignore[arg-type]
            ScalingSpeed(None, 50),  # type: ignore[arg-type]
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
        ("raw", "value"),
        [
            ((0x00, 0x00, 0xFF), ScalingSpeed(0, 100)),  # time period 0
            ((0x00, 0x28, 0x00), ScalingSpeed(4000, 0)),  # percent 0
            ((0x00, 0x00, 0x00), ScalingSpeed(0, 0)),
            ((0x00, 0x28, 0x01), ScalingSpeed(4000, 0)),  # 0,4 % rounds to 0
        ],
    )
    def test_from_knx_out_of_range(
        self, raw: tuple[int, ...], value: ScalingSpeed
    ) -> None:
        """Test DPTScalingSpeed parsing of out of range values is lenient."""
        assert DPTScalingSpeed.from_knx(DPTArray(raw)) == value

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
                "type": "integer",
                "required": True,
                "value_min": 1,
                "value_max": 100,
            },
        ]


class TestDPTScalingStepTime:
    """Test class for KNX DPTScalingStepTime (225.002) objects."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            # spec examples
            (ScalingStepTime(15, 100), (0x00, 0x0F, 0xFF)),
            (ScalingStepTime(31, 100), (0x00, 0x1F, 0xFF)),
            # limits
            (ScalingStepTime(1, 1), (0x00, 0x01, 0x03)),
            (ScalingStepTime(65_535, 100), (0xFF, 0xFF, 0xFF)),
            (ScalingStepTime(256, 50), (0x01, 0x00, 0x80)),
        ],
    )
    def test_value(self, value: ScalingStepTime, raw: tuple[int, ...]) -> None:
        """Test DPTScalingStepTime parsing and streaming."""
        knx_value = DPTScalingStepTime.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert DPTScalingStepTime.from_knx(knx_value) == value

    def test_spec_example_percent(self) -> None:
        """75 % of the spec example (C0h) is encoded like DPT 5.001 (BFh)."""
        assert DPTScalingStepTime.from_knx(
            DPTArray((0x00, 0x3E, 0xC0))
        ) == ScalingStepTime(62, 75)
        assert DPTScalingStepTime.to_knx(ScalingStepTime(62, 75)) == DPTArray(
            (0x00, 0x3E, 0xBF)
        )

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
            ScalingStepTime(15, 0),
            ScalingStepTime(15, 101),
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
        ("raw", "value"),
        [
            ((0x00, 0x00, 0xFF), ScalingStepTime(0, 100)),  # time period 0
            ((0x00, 0x0F, 0x00), ScalingStepTime(15, 0)),  # percent 0
        ],
    )
    def test_from_knx_out_of_range(
        self, raw: tuple[int, ...], value: ScalingStepTime
    ) -> None:
        """Test DPTScalingStepTime parsing of out of range values is lenient."""
        assert DPTScalingStepTime.from_knx(DPTArray(raw)) == value

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
                "type": "integer",
                "required": True,
                "value_min": 1,
                "value_max": 100,
            },
        ]
