"""Implementation of KNX scaling speed data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary

RANGE_PERCENT: dict[str, int] = {"value_min": 0, "value_max": 100}
RANGE_TIME_PERIOD_S: dict[str, float] = {
    "value_min": 0.1,
    "value_max": 6553.5,
    "resolution": 0.1,
}


@dataclass(slots=True)
class ScalingSpeed(DPTComplexData):
    """
    Representation of a scaling value together with a time period (KNX DPT_ScalingSpeed).

    `time_period`: time in seconds, 0.1..6553.5 (resolution 0.1 s;
        see also DPT_TimePeriod100Msec, DPT_ID 7.004).
    `percent`: percent value, 0..100 (see also DPT_Scaling, DPT_ID 5.001).

    Note: KNX v02.02.01 - System Specifications 03.07.02 - §3.44.1 defines this DPT to
    encode a dimming *speed* - `percent` divided by `time_period` - rather than
    "go to `percent` over `time_period` seconds". In practice actuators supporting
    combined value/dimming-time objects (e.g. DALI gateways) use it exactly the
    latter way: dim to `percent` brightness, reaching it after `time_period` seconds.
    """

    time_period: float = field(metadata=RANGE_TIME_PERIOD_S)
    percent: float = field(metadata=RANGE_PERCENT)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ScalingSpeed:
        """Init from a dictionary."""
        try:
            time_period = float(data["time_period"])
            percent = float(data["percent"])
        except KeyError as err:
            raise ValueError(f"Missing required key: {err}") from err
        except (TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for ScalingSpeed: {err}") from err

        return cls(time_period=time_period, percent=percent)

    def as_dict(self) -> dict[str, float]:
        """Create a JSON serializable dictionary."""
        return {
            "time_period": self.time_period,
            "percent": self.percent,
        }


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

        time_period_raw = raw[0] << 8 | raw[1]
        percent_raw = raw[2]

        return ScalingSpeed(
            time_period=round(time_period_raw * 0.1, 1),
            percent=round(percent_raw / 255 * 100),
        )

    @classmethod
    def _to_knx(cls, value: ScalingSpeed) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not 0.1 <= value.time_period <= 6553.5:
            raise ValueError(
                f"Time period out of range 0.1..6553.5 s: {value.time_period}"
            )
        if not 0 <= value.percent <= 100:
            raise ValueError(f"Percent value out of range 0..100: {value.percent}")

        time_period_raw = round(value.time_period * 10)
        percent_raw = round(value.percent / 100 * 255)

        return DPTArray(
            (
                time_period_raw >> 8,
                time_period_raw & 0xFF,
                percent_raw,
            )
        )
