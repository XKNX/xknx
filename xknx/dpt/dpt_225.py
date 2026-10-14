"""
Implementation of KNX scaling speed and scaling step time data point types.

KNX v02.02.01 - Datapoint Types 03.07.02 - §3.44.1 / §3.44.2
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields as dataclass_fields
from typing import Any, Final, Self

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary

# Percent field: [0,4 … 100] % encoded like DPT_Scaling (5.001), 0x01..0xFF
_PERCENT_MIN: Final = 0.4
_PERCENT_MAX: Final = 100.0
_PERCENT_METADATA: Final[dict[str, float]] = {
    "value_min": _PERCENT_MIN,
    "value_max": _PERCENT_MAX,
    "resolution": 0.4,
}


class _TimePeriodPercent(DPTComplexData):
    """Base for the U16U8 DPTs carrying a `time_period` and a `percent` field."""

    __slots__ = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Init from a dictionary."""
        result: dict[str, int | float] = {}
        for key, parse in (("time_period", int), ("percent", float)):
            value = data.get(key)
            if value is None:
                raise ValueError(f"Missing value for {key}")
            try:
                result[key] = parse(value)
            except (TypeError, ValueError) as err:
                raise ValueError(f"Invalid value for {key}: {err}") from err
        return cls(**result)

    def as_dict(self) -> dict[str, int | float]:
        """Create a JSON serializable dictionary."""
        return {
            field_.name: getattr(self, field_.name) for field_ in dataclass_fields(self)
        }


@dataclass(slots=True)
class ScalingSpeed(_TimePeriodPercent):
    """
    Representation of a scaling speed (DPT 225.001).

    `time_period`: int 100..6_553_500 ms (resolution 100 ms).
    `percent`: float 0.4..100 % (resolution 100/255 %).
    The speed is `percent` / `time_period`.
    """

    time_period: int = field(
        metadata={"value_min": 100, "value_max": 6_553_500, "resolution": 100}
    )
    percent: float = field(metadata=_PERCENT_METADATA)


@dataclass(slots=True)
class ScalingStepTime(_TimePeriodPercent):
    """
    Representation of a scaling step time (DPT 225.002).

    `time_period`: int 1..65_535 ms - time per DPT_Scaling resolution step.
    `percent`: float 0.4..100 % (resolution 100/255 %) - upper end of the
        range the `time_period` is valid for.
    """

    time_period: int = field(metadata={"value_min": 1, "value_max": 65_535})
    percent: float = field(metadata=_PERCENT_METADATA)


def _decode_percent(raw: int) -> float:
    """Decode the U8 percent field; 1 decimal keeps every raw value distinct."""
    return round(raw / 255 * 100, 1)


def _encode_percent(percent: float) -> int:
    """Encode the percent field to U8."""
    if not _PERCENT_MIN <= percent <= _PERCENT_MAX:
        raise ValueError(
            f"Percent out of range {_PERCENT_MIN}..{_PERCENT_MAX} %: {percent}"
        )
    return round(percent / 100 * 255)


def _validate_raw(raw: tuple[int, ...]) -> None:
    """Reject the out of range raw value 0 of either field."""
    if not raw[0] << 8 | raw[1]:
        raise ValueError("Time period 0 is out of range")
    if not raw[2]:
        raise ValueError("Percent 0 is out of range")


class DPTScalingSpeed(DPTComplex[ScalingSpeed]):
    """Abstraction for KNX 3 octet scaling speed (DPT 225.001)."""

    data_type = ScalingSpeed
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 225
    dpt_sub_number = 1
    value_type = "scaling_speed"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ScalingSpeed:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        try:
            _validate_raw(raw)
        except ValueError as err:
            raise ConversionError(
                f"Could not parse {cls.dpt_name()}: {err}", payload=payload
            ) from err
        return ScalingSpeed(
            time_period=(raw[0] << 8 | raw[1]) * 100,
            percent=_decode_percent(raw[2]),
        )

    @classmethod
    def _to_knx(cls, value: ScalingSpeed) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not 100 <= value.time_period <= 6_553_500:
            raise ValueError(
                f"Time period out of range 100..6553500 ms: {value.time_period}"
            )
        time_period = round(value.time_period / 100)
        return DPTArray(
            (time_period >> 8, time_period & 0xFF, _encode_percent(value.percent))
        )


class DPTScalingStepTime(DPTComplex[ScalingStepTime]):
    """Abstraction for KNX 3 octet scaling step time (DPT 225.002)."""

    data_type = ScalingStepTime
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 225
    dpt_sub_number = 2
    value_type = "scaling_step_time"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ScalingStepTime:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        try:
            _validate_raw(raw)
        except ValueError as err:
            raise ConversionError(
                f"Could not parse {cls.dpt_name()}: {err}", payload=payload
            ) from err
        return ScalingStepTime(
            time_period=raw[0] << 8 | raw[1],
            percent=_decode_percent(raw[2]),
        )

    @classmethod
    def _to_knx(cls, value: ScalingStepTime) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not 1 <= value.time_period <= 65_535:
            raise ValueError(
                f"Time period out of range 1..65535 ms: {value.time_period}"
            )
        return DPTArray(
            (
                value.time_period >> 8,
                value.time_period & 0xFF,
                _encode_percent(value.percent),
            )
        )
