"""Implementation of the KNX 273 data point types (forecasts for F16 values)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData, DPTComplexFieldSchema
from .dpt_5 import DPTScaling
from .dpt_7 import DPTTimePeriodMin
from .dpt_9 import (
    DPT2ByteFloat,
    DPTConcentrationUGM3,
    DPTHumidity,
    DPTPartsPerMillion,
    DPTPowerDensity,
    DPTTemperature,
    DPTWsp,
)
from .payload import DPTArray, DPTBinary

# 7FFFh denotes invalid data for DPT 9 - also sent for fields marked invalid
_INVALID_F16 = (0x7F, 0xFF)
_F16_RANGE = {
    "value_min": DPT2ByteFloat.value_min,
    "value_max": DPT2ByteFloat.value_max,
    "resolution": DPT2ByteFloat.resolution,
}
_VALUE_FIELDS = ("maximum_value", "minimum_value")

_DELAY_TIME_VALID = 0b1000
_PROBABILITY_VALID = 0b0100
_MAXIMUM_VALUE_VALID = 0b0010
_MINIMUM_VALUE_VALID = 0b0001


@dataclass(slots=True)
class Forecast(DPTComplexData):
    """
    Representation of a weather forecast for a 2-octet float value.

    `delay_time`: int 1..65535 minutes until the forecast applies; None if invalid
    `probability`: int 0..100 percent; None if invalid
    `maximum_value`: float in the unit of the subtype; None if invalid
    `minimum_value`: float in the unit of the subtype; None if invalid
    """

    delay_time: int | None = field(
        default=None, metadata={"value_min": 1, "value_max": 65_535}
    )
    probability: int | None = field(
        default=None, metadata={"value_min": 0, "value_max": 100}
    )
    maximum_value: float | None = field(default=None, metadata=_F16_RANGE)
    minimum_value: float | None = field(default=None, metadata=_F16_RANGE)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Forecast:
        """Init from a dictionary."""
        try:
            delay_time = data.get("delay_time")
            probability = data.get("probability")
            maximum_value = data.get("maximum_value")
            minimum_value = data.get("minimum_value")
        except AttributeError as err:
            raise ValueError(f"Invalid value for Forecast: {err}") from err
        try:
            return cls(
                delay_time=int(delay_time) if delay_time is not None else None,
                probability=int(probability) if probability is not None else None,
                maximum_value=(
                    float(maximum_value) if maximum_value is not None else None
                ),
                minimum_value=(
                    float(minimum_value) if minimum_value is not None else None
                ),
            )
        except (TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for Forecast: {err}") from err

    def as_dict(self) -> dict[str, int | float | None]:
        """Create a JSON serializable dictionary."""
        return {
            "delay_time": self.delay_time,
            "probability": self.probability,
            "maximum_value": self.maximum_value,
            "minimum_value": self.minimum_value,
        }


def _check_minimum_maximum(value: Forecast) -> None:
    """Raise ConversionError if the maximum value is lower than the minimum value."""
    if (
        value.maximum_value is not None
        and value.minimum_value is not None
        and value.maximum_value < value.minimum_value
    ):
        raise ConversionError("Maximum value is lower than minimum value", value=value)


def _f16_from_knx(
    raw: tuple[int, ...], value_transcoder: type[DPT2ByteFloat]
) -> float | None:
    """Parse a 2-octet float value; None for invalid data."""
    if raw == _INVALID_F16:
        return None
    return value_transcoder.from_knx(DPTArray(raw))


def _forecast_from_knx(
    raw: tuple[int, ...], value_transcoder: type[DPT2ByteFloat]
) -> Forecast:
    """Parse a forecast; fields with a validity bit of 0 are None."""
    mask = raw[0]
    delay_time = None
    if mask & _DELAY_TIME_VALID:
        delay_time = DPTTimePeriodMin.from_knx(DPTArray(raw[1:3]))
        if delay_time < 1:
            raise ConversionError("Delay time out of range 1..65535", raw=raw)
    value = Forecast(
        delay_time=delay_time,
        probability=(
            DPTScaling.from_knx(DPTArray(raw[3:4]))
            if mask & _PROBABILITY_VALID
            else None
        ),
        maximum_value=(
            _f16_from_knx(raw[4:6], value_transcoder)
            if mask & _MAXIMUM_VALUE_VALID
            else None
        ),
        minimum_value=(
            _f16_from_knx(raw[6:8], value_transcoder)
            if mask & _MINIMUM_VALUE_VALID
            else None
        ),
    )
    _check_minimum_maximum(value)
    return value


def _forecast_to_knx(
    value: Forecast, value_transcoder: type[DPT2ByteFloat]
) -> DPTArray:
    """Serialize a forecast; invalid fields are sent as 0 (7FFFh for values)."""
    _check_minimum_maximum(value)
    if value.delay_time is not None and value.delay_time < 1:
        raise ConversionError("Delay time out of range 1..65535", value=value)
    delay_time = (
        DPTTimePeriodMin.to_knx(value.delay_time).value
        if value.delay_time is not None
        else (0, 0)
    )
    probability = (
        DPTScaling.to_knx(value.probability).value
        if value.probability is not None
        else (0,)
    )
    maximum_value = (
        value_transcoder.to_knx(value.maximum_value).value
        if value.maximum_value is not None
        else _INVALID_F16
    )
    minimum_value = (
        value_transcoder.to_knx(value.minimum_value).value
        if value.minimum_value is not None
        else _INVALID_F16
    )
    mask = (
        (value.delay_time is not None) << 3
        | (value.probability is not None) << 2
        | (value.maximum_value is not None) << 1
        | (value.minimum_value is not None)
    )
    return DPTArray((mask, *delay_time, *probability, *maximum_value, *minimum_value))


def _forecast_dict_schema(
    value_transcoder: type[DPT2ByteFloat],
) -> list[DPTComplexFieldSchema]:
    """Return the Forecast schema with the value range of the subtype."""
    schema = Forecast.get_dict_schema()
    for entry in schema:
        if entry["name"] in _VALUE_FIELDS:
            entry["value_min"] = value_transcoder.value_min
            entry["value_max"] = value_transcoder.value_max
    return schema


class DPTForecastTemperature(DPTComplex[Forecast]):
    """
    Abstraction for KNX 8 octet temperature forecast (DPT 273.001).

    Minimum and maximum value according to DPT 9.001 (°C).
    KNX v02.02.01 - Datapoint Types 03.07.02 - §10.1
    """

    data_type = Forecast
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 273
    dpt_sub_number = 1
    value_type = "forecast_temperature"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> Forecast:
        """Parse/deserialize from KNX/IP raw data."""
        return _forecast_from_knx(cls.validate_payload(payload), DPTTemperature)

    @classmethod
    def _to_knx(cls, value: Forecast) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _forecast_to_knx(value, DPTTemperature)

    @classmethod
    def get_dict_schema(cls) -> list[DPTComplexFieldSchema]:
        """Return schema for the dict used in to_knx() / from_knx()."""
        return _forecast_dict_schema(DPTTemperature)


class DPTForecastWindSpeed(DPTComplex[Forecast]):
    """
    Abstraction for KNX 8 octet wind speed forecast (DPT 273.002).

    Minimum and maximum value according to DPT 9.005 (m/s).
    KNX v02.02.01 - Datapoint Types 03.07.02 - §10.1
    """

    data_type = Forecast
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 273
    dpt_sub_number = 2
    value_type = "forecast_wind_speed"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> Forecast:
        """Parse/deserialize from KNX/IP raw data."""
        return _forecast_from_knx(cls.validate_payload(payload), DPTWsp)

    @classmethod
    def _to_knx(cls, value: Forecast) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _forecast_to_knx(value, DPTWsp)

    @classmethod
    def get_dict_schema(cls) -> list[DPTComplexFieldSchema]:
        """Return schema for the dict used in to_knx() / from_knx()."""
        return _forecast_dict_schema(DPTWsp)


class DPTForecastRelativeHumidity(DPTComplex[Forecast]):
    """
    Abstraction for KNX 8 octet relative humidity forecast (DPT 273.003).

    Minimum and maximum value according to DPT 9.007 (%).
    KNX v02.02.01 - Datapoint Types 03.07.02 - §10.1
    """

    data_type = Forecast
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 273
    dpt_sub_number = 3
    value_type = "forecast_relative_humidity"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> Forecast:
        """Parse/deserialize from KNX/IP raw data."""
        return _forecast_from_knx(cls.validate_payload(payload), DPTHumidity)

    @classmethod
    def _to_knx(cls, value: Forecast) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _forecast_to_knx(value, DPTHumidity)

    @classmethod
    def get_dict_schema(cls) -> list[DPTComplexFieldSchema]:
        """Return schema for the dict used in to_knx() / from_knx()."""
        return _forecast_dict_schema(DPTHumidity)


class DPTForecastAbsoluteHumidity(DPTComplex[Forecast]):
    """
    Abstraction for KNX 8 octet absolute humidity forecast (DPT 273.004).

    The spec refers to DPT 9.007 (%) for minimum and maximum value.
    KNX v02.02.01 - Datapoint Types 03.07.02 - §10.1
    """

    data_type = Forecast
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 273
    dpt_sub_number = 4
    value_type = "forecast_absolute_humidity"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> Forecast:
        """Parse/deserialize from KNX/IP raw data."""
        return _forecast_from_knx(cls.validate_payload(payload), DPTHumidity)

    @classmethod
    def _to_knx(cls, value: Forecast) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _forecast_to_knx(value, DPTHumidity)

    @classmethod
    def get_dict_schema(cls) -> list[DPTComplexFieldSchema]:
        """Return schema for the dict used in to_knx() / from_knx()."""
        return _forecast_dict_schema(DPTHumidity)


class DPTForecastCO2(DPTComplex[Forecast]):
    """
    Abstraction for KNX 8 octet CO2 forecast (DPT 273.005).

    Minimum and maximum value according to DPT 9.008 (ppm).
    KNX v02.02.01 - Datapoint Types 03.07.02 - §10.1
    """

    data_type = Forecast
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 273
    dpt_sub_number = 5
    value_type = "forecast_co2"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> Forecast:
        """Parse/deserialize from KNX/IP raw data."""
        return _forecast_from_knx(cls.validate_payload(payload), DPTPartsPerMillion)

    @classmethod
    def _to_knx(cls, value: Forecast) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _forecast_to_knx(value, DPTPartsPerMillion)

    @classmethod
    def get_dict_schema(cls) -> list[DPTComplexFieldSchema]:
        """Return schema for the dict used in to_knx() / from_knx()."""
        return _forecast_dict_schema(DPTPartsPerMillion)


class DPTForecastAirPollutants(DPTComplex[Forecast]):
    """
    Abstraction for KNX 8 octet air pollutants forecast (DPT 273.006).

    Minimum and maximum value according to DPT 9.030 (μg/m³).
    KNX v02.02.01 - Datapoint Types 03.07.02 - §10.1
    """

    data_type = Forecast
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 273
    dpt_sub_number = 6
    value_type = "forecast_air_pollutants"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> Forecast:
        """Parse/deserialize from KNX/IP raw data."""
        return _forecast_from_knx(cls.validate_payload(payload), DPTConcentrationUGM3)

    @classmethod
    def _to_knx(cls, value: Forecast) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _forecast_to_knx(value, DPTConcentrationUGM3)

    @classmethod
    def get_dict_schema(cls) -> list[DPTComplexFieldSchema]:
        """Return schema for the dict used in to_knx() / from_knx()."""
        return _forecast_dict_schema(DPTConcentrationUGM3)


class DPTForecastSunIntensity(DPTComplex[Forecast]):
    """
    Abstraction for KNX 8 octet sun intensity forecast (DPT 273.007).

    Minimum and maximum value according to DPT 9.022 (W/m²).
    KNX v02.02.01 - Datapoint Types 03.07.02 - §10.1
    """

    data_type = Forecast
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 273
    dpt_sub_number = 7
    value_type = "forecast_sun_intensity"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> Forecast:
        """Parse/deserialize from KNX/IP raw data."""
        return _forecast_from_knx(cls.validate_payload(payload), DPTPowerDensity)

    @classmethod
    def _to_knx(cls, value: Forecast) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _forecast_to_knx(value, DPTPowerDensity)

    @classmethod
    def get_dict_schema(cls) -> list[DPTComplexFieldSchema]:
        """Return schema for the dict used in to_knx() / from_knx()."""
        return _forecast_dict_schema(DPTPowerDensity)
