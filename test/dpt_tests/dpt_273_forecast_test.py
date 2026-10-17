"""Unit test for KNX DPT 273 objects."""

from typing import Any

import pytest

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.dpt.dpt_273 import (
    DPTForecastAbsoluteHumidity,
    DPTForecastAirPollutants,
    DPTForecastCO2,
    DPTForecastRelativeHumidity,
    DPTForecastSunIntensity,
    DPTForecastTemperature,
    DPTForecastWindSpeed,
    Forecast,
)
from xknx.exceptions import ConversionError, CouldNotParseTelegram

ALL_FORECASTS = [
    DPTForecastTemperature,
    DPTForecastWindSpeed,
    DPTForecastRelativeHumidity,
    DPTForecastAbsoluteHumidity,
    DPTForecastCO2,
    DPTForecastAirPollutants,
    DPTForecastSunIntensity,
]


class TestForecast:
    """Test Forecast class."""

    @pytest.mark.parametrize(
        ("data", "value"),
        [
            (
                {
                    "delay_time": 60,
                    "probability": 50,
                    "maximum_value": 25.5,
                    "minimum_value": -3.2,
                },
                Forecast(60, 50, 25.5, -3.2),
            ),
            ({"delay_time": 1}, Forecast(delay_time=1)),
            ({"probability": "100"}, Forecast(probability=100)),
            ({"maximum_value": 1}, Forecast(maximum_value=1.0)),
            ({"minimum_value": "2.5"}, Forecast(minimum_value=2.5)),
            ({"delay_time": None}, Forecast()),
            ({}, Forecast()),
        ],
    )
    def test_dict(self, data: dict[str, Any], value: Forecast) -> None:
        """Test from_dict and as_dict methods."""
        assert Forecast.from_dict(data) == value
        assert Forecast.from_dict(value.as_dict()) == value
        assert value.as_dict().keys() == {
            "delay_time",
            "probability",
            "maximum_value",
            "minimum_value",
        }

    @pytest.mark.parametrize(
        "data",
        [
            {"delay_time": "a"},
            {"probability": "a"},
            {"maximum_value": "a"},
            {"minimum_value": [1]},
            1,
        ],
    )
    def test_dict_invalid(self, data: Any) -> None:
        """Test from_dict with invalid data."""
        with pytest.raises(ValueError):
            Forecast.from_dict(data)


@pytest.mark.parametrize("dpt", ALL_FORECASTS)
class TestDPTForecastCommon:
    """Test layout shared by all DPT 273 subtypes."""

    @pytest.mark.parametrize(
        ("value", "raw"),
        [
            (
                Forecast(),
                (0x00, 0x00, 0x00, 0x00, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
            (
                Forecast(delay_time=60),
                (0x08, 0x00, 0x3C, 0x00, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
            (
                Forecast(probability=100),
                (0x04, 0x00, 0x00, 0xFF, 0x7F, 0xFF, 0x7F, 0xFF),
            ),
            (
                Forecast(maximum_value=25.5),
                (0x02, 0x00, 0x00, 0x00, 0x0C, 0xFB, 0x7F, 0xFF),
            ),
            (
                Forecast(minimum_value=20.48),
                (0x01, 0x00, 0x00, 0x00, 0x7F, 0xFF, 0x0C, 0x00),
            ),
            (
                Forecast(1, 0, 0.0, 0.0),
                (0x0F, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00),
            ),
            (
                Forecast(65_535, 50, 25.5, 20.48),
                (0x0F, 0xFF, 0xFF, 0x80, 0x0C, 0xFB, 0x0C, 0x00),
            ),
            (
                Forecast(60, 100, 25.5, 25.5),
                (0x0F, 0x00, 0x3C, 0xFF, 0x0C, 0xFB, 0x0C, 0xFB),
            ),
        ],
    )
    def test_value(
        self, dpt: type[DPTBase], value: Forecast, raw: tuple[int, ...]
    ) -> None:
        """Test parsing and streaming."""
        knx_value = dpt.to_knx(value)
        assert knx_value == DPTArray(raw)
        assert dpt.from_knx(knx_value) == value

    def test_to_knx_from_dict(self, dpt: type[DPTBase]) -> None:
        """Test serializing a dict."""
        assert dpt.to_knx(
            {"delay_time": 60, "probability": 50, "maximum_value": 25.5}
        ) == DPTArray((0x0E, 0x00, 0x3C, 0x80, 0x0C, 0xFB, 0x7F, 0xFF))

    @pytest.mark.parametrize(
        ("raw", "value"),
        [
            # reserved bits ignored
            (
                (0xF0, 0x00, 0x3C, 0x80, 0x0C, 0xFB, 0x0C, 0x00),
                Forecast(),
            ),
            (
                (0xFF, 0x00, 0x3C, 0x80, 0x0C, 0xFB, 0x0C, 0x00),
                Forecast(60, 50, 25.5, 20.48),
            ),
            # fields with validity bit 0 are ignored
            (
                (0x00, 0x00, 0x00, 0xFF, 0x80, 0x00, 0x00, 0x00),
                Forecast(),
            ),
            # 7FFFh invalid data
            (
                (0x03, 0x00, 0x00, 0x00, 0x7F, 0xFF, 0x7F, 0xFF),
                Forecast(),
            ),
            (
                (0x03, 0x00, 0x00, 0x00, 0x7F, 0xFF, 0x0C, 0x00),
                Forecast(minimum_value=20.48),
            ),
            # minimum higher than an invalid maximum
            (
                (0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x00),
                Forecast(minimum_value=20.48),
            ),
        ],
    )
    def test_from_knx(
        self, dpt: type[DPTBase], raw: tuple[int, ...], value: Forecast
    ) -> None:
        """Test parsing of mask bits."""
        assert dpt.from_knx(DPTArray(raw)) == value

    @pytest.mark.parametrize(
        "raw",
        [
            # maximum lower than minimum
            (0x03, 0x00, 0x00, 0x00, 0x0C, 0x00, 0x0C, 0xFB),
            # delay time 0
            (0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
        ],
    )
    def test_from_knx_invalid(self, dpt: type[DPTBase], raw: tuple[int, ...]) -> None:
        """Test parsing invalid values."""
        with pytest.raises(ConversionError):
            dpt.from_knx(DPTArray(raw))

    @pytest.mark.parametrize(
        "value",
        [
            Forecast(delay_time=0),
            Forecast(delay_time=65_536),
            Forecast(probability=-1),
            Forecast(probability=101),
            Forecast(maximum_value=670_433.29),
            Forecast(minimum_value=-671_088.65),
            Forecast(maximum_value=1.0, minimum_value=2.0),
            Forecast(delay_time="a"),  # type: ignore[arg-type]
            {"probability": "a"},
            {"maximum_value": 1, "minimum_value": 2},
            None,
            1,
        ],
    )
    def test_to_knx_invalid(self, dpt: type[DPTBase], value: Any) -> None:
        """Test serializing invalid values."""
        with pytest.raises(ConversionError):
            dpt.to_knx(value)

    @pytest.mark.parametrize(
        "payload",
        [
            DPTArray((0x00,) * 7),
            DPTArray((0x00,) * 9),
            DPTBinary(0),
        ],
    )
    def test_from_knx_wrong_payload(
        self, dpt: type[DPTBase], payload: DPTArray | DPTBinary
    ) -> None:
        """Test parsing wrong payloads."""
        with pytest.raises(CouldNotParseTelegram):
            dpt.from_knx(payload)

    def test_parse_transcoder(self, dpt: type[DPTBase]) -> None:
        """Test lookup by DPT number and value_type."""
        assert DPTBase.parse_transcoder(f"273.{dpt.dpt_sub_number:03}") is dpt
        assert dpt.value_type is not None
        assert DPTBase.parse_transcoder(dpt.value_type) is dpt


@pytest.mark.parametrize(
    ("dpt", "sub", "value_type", "value_min"),
    [
        (DPTForecastTemperature, 1, "forecast_temperature", -273),
        (DPTForecastWindSpeed, 2, "forecast_wind_speed", 0),
        (DPTForecastRelativeHumidity, 3, "forecast_relative_humidity", 0),
        (DPTForecastAbsoluteHumidity, 4, "forecast_absolute_humidity", 0),
        (DPTForecastCO2, 5, "forecast_co2", 0),
        (DPTForecastAirPollutants, 6, "forecast_air_pollutants", 0),
        (DPTForecastSunIntensity, 7, "forecast_sun_intensity", -671_088.64),
    ],
)
class TestDPTForecastSubtypes:
    """Test subtype specific value ranges."""

    def test_numbers(
        self,
        dpt: type[DPTBase],
        sub: int,
        value_type: str,
        value_min: float,
    ) -> None:
        """Test DPT numbers and value_type."""
        assert dpt.dpt_main_number == 273
        assert dpt.dpt_sub_number == sub
        assert dpt.value_type == value_type
        assert dpt.payload_length == 8

    def test_get_dict_schema(
        self,
        dpt: type[DPTForecastTemperature],
        sub: int,
        value_type: str,
        value_min: float,
    ) -> None:
        """Test get_dict_schema with the value range of the subtype."""
        value_schema = {
            "type": "float",
            "required": False,
            "value_min": value_min,
            "value_max": 670_433.28,
            "resolution": 0.01,
        }
        assert dpt.get_dict_schema() == [
            {
                "name": "delay_time",
                "type": "integer",
                "required": False,
                "value_min": 1,
                "value_max": 65_535,
            },
            {
                "name": "probability",
                "type": "integer",
                "required": False,
                "value_min": 0,
                "value_max": 100,
            },
            {"name": "maximum_value", **value_schema},
            {"name": "minimum_value", **value_schema},
        ]

    def test_value_min(
        self,
        dpt: type[DPTBase],
        sub: int,
        value_type: str,
        value_min: float,
    ) -> None:
        """Test the lower boundary of minimum and maximum value."""
        dpt.to_knx(Forecast(maximum_value=value_min, minimum_value=value_min))
        if value_min > -671_088.64:
            with pytest.raises(ConversionError):
                dpt.to_knx(Forecast(minimum_value=value_min - 1))
            # -300.0 (A0ADh) and -10.0 (8418h) are below the subtype range
            below = (0xA0, 0xAD) if value_min < -10 else (0x84, 0x18)
            with pytest.raises(ConversionError):
                dpt.from_knx(DPTArray((0x01, 0x00, 0x00, 0x00, 0x7F, 0xFF, *below)))
