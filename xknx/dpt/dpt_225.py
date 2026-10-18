"""Implementation of KNX scaling speed and scaling step time data point types."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields as dataclass_fields
from typing import Any, Final, Self

from .dpt import DPTComplex, DPTComplexData
from .dpt_5 import DPTScaling
from .dpt_7 import DPT2ByteUnsigned, DPTTimePeriod100Msec, DPTTimePeriodMsec
from .payload import DPTArray, DPTBinary

# percent is encoded like DPT 5.001; the specified range starts at 0,4 % (raw 1)
_PERCENT_METADATA: Final[dict[str, int]] = {"value_min": 1, "value_max": 100}


class _TimePeriodPercent(DPTComplexData):
    """Base for the U16U8 DPTs carrying a `time_period` and a `percent` field."""

    __slots__ = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Init from a dictionary."""
        result: dict[str, int] = {}
        for key in ("time_period", "percent"):
            try:
                value = data.get(key)
            except AttributeError as err:
                raise ValueError(f"Invalid value for {cls.__name__}: {err}") from err
            if value is None:
                raise ValueError(f"Missing value for {key}")
            try:
                result[key] = int(value)
            except (TypeError, ValueError) as err:
                raise ValueError(f"Invalid value for {key}: {err}") from err
        return cls(**result)

    def as_dict(self) -> dict[str, int]:
        """Create a JSON serializable dictionary."""
        return {
            field_.name: getattr(self, field_.name) for field_ in dataclass_fields(self)
        }


@dataclass(slots=True)
class ScalingSpeed(_TimePeriodPercent):
    """
    Representation of a scaling speed (DPT 225.001).

    `time_period`: int 100..6_553_500 ms (resolution 100 ms).
    `percent`: int 1..100 %.
    The speed is `percent` / `time_period`.
    """

    time_period: int = field(
        metadata={"value_min": 100, "value_max": 6_553_500, "resolution": 100}
    )
    percent: int = field(metadata=_PERCENT_METADATA)


@dataclass(slots=True)
class ScalingStepTime(_TimePeriodPercent):
    """
    Representation of a scaling step time (DPT 225.002).

    `time_period`: int 1..65_535 ms - time per DPT_Scaling resolution step.
    `percent`: int 1..100 % - upper end of the range the `time_period` is valid for.
    """

    time_period: int = field(metadata={"value_min": 1, "value_max": 65_535})
    percent: int = field(metadata=_PERCENT_METADATA)


def _decode(
    raw: tuple[int, ...], time_transcoder: type[DPT2ByteUnsigned]
) -> tuple[int, int]:
    """Decode time period and percent; a raw 0 is decoded although out of range."""
    return (
        time_transcoder.from_knx(DPTArray(raw[0:2])),
        DPTScaling.from_knx(DPTArray((raw[2],))),
    )


def _encode(
    value: ScalingSpeed | ScalingStepTime, time_transcoder: type[DPT2ByteUnsigned]
) -> DPTArray:
    """Encode time period and percent; a raw 0 is out of the specified range."""
    raw_time_period = time_transcoder.to_knx(value.time_period).value
    raw_percent = DPTScaling.to_knx(value.percent).value
    if raw_time_period == (0, 0):
        raise ValueError(f"Time period out of range: {value}")
    if raw_percent == (0,):
        raise ValueError(f"Percent out of range: {value}")
    return DPTArray((*raw_time_period, *raw_percent))


class DPTScalingSpeed(DPTComplex[ScalingSpeed]):
    """
    Abstraction for KNX 3 octet scaling speed (DPT 225.001).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.44.1
    The time period is encoded like DPT 7.004, the percent like DPT 5.001.
    """

    data_type = ScalingSpeed
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 225
    dpt_sub_number = 1
    value_type = "scaling_speed"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ScalingSpeed:
        """Parse/deserialize from KNX/IP raw data."""
        time_period, percent = _decode(
            cls.validate_payload(payload), DPTTimePeriod100Msec
        )
        return ScalingSpeed(time_period=time_period, percent=percent)

    @classmethod
    def _to_knx(cls, value: ScalingSpeed) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _encode(value, DPTTimePeriod100Msec)


class DPTScalingStepTime(DPTComplex[ScalingStepTime]):
    """
    Abstraction for KNX 3 octet scaling step time (DPT 225.002).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.44.2
    The time period is encoded like DPT 7.002, the percent like DPT 5.001.
    Not allowed for run-time communication: only for parameters and diagnostic
    data, or where a function block specification says so.
    """

    data_type = ScalingStepTime
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 225
    dpt_sub_number = 2
    value_type = "scaling_step_time"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ScalingStepTime:
        """Parse/deserialize from KNX/IP raw data."""
        time_period, percent = _decode(cls.validate_payload(payload), DPTTimePeriodMsec)
        return ScalingStepTime(time_period=time_period, percent=percent)

    @classmethod
    def _to_knx(cls, value: ScalingStepTime) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _encode(value, DPTTimePeriodMsec)
