"""Implementation of the KNX 255 data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData
from .dpt_14 import DPT4ByteFloat
from .payload import DPTArray, DPTBinary

_LONGITUDE_RANGE = {"value_min": -180.0, "value_max": 180.0}
_LATITUDE_RANGE = {"value_min": -90.0, "value_max": 90.0}


@dataclass(slots=True)
class GeographicalLocation(DPTComplexData):
    """
    Representation of a geographical location.

    `longitude`: float -180..180 degrees
    `latitude`: float -90..90 degrees

    The spec gives the range of both fields as "See F32"; the limits of
    ±180° and ±90° are an xknx addition.
    """

    longitude: float = field(metadata=_LONGITUDE_RANGE)
    latitude: float = field(metadata=_LATITUDE_RANGE)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> GeographicalLocation:
        """Init from a dictionary."""
        result = {}
        for name in ("longitude", "latitude"):
            try:
                result[name] = float(data[name])
            except (KeyError, TypeError, ValueError) as err:
                raise ValueError(f"Invalid value for {name}: {err}") from err
        return cls(**result)

    def as_dict(self) -> dict[str, float]:
        """Create a JSON serializable dictionary."""
        return {
            "longitude": self.longitude,
            "latitude": self.latitude,
        }


def _check_range(value: GeographicalLocation) -> None:
    """Raise ConversionError if a coordinate is out of range or not a number."""
    for name, coordinate, limits in (
        ("longitude", value.longitude, _LONGITUDE_RANGE),
        ("latitude", value.latitude, _LATITUDE_RANGE),
    ):
        if not limits["value_min"] <= coordinate <= limits["value_max"]:
            raise ConversionError(
                f"{name} out of range {limits['value_min']}..{limits['value_max']}",
                value=value,
            )


class DPTGeographicalLocation(DPTComplex[GeographicalLocation]):
    """
    Abstraction for KNX 8 octet geographical location (DPT 255.001).

    Longitude and latitude in degrees, each as IEEE 754 single precision float.
    KNX v02.02.01 - Datapoint Types 03.07.02 - §3.52.1
    """

    data_type = GeographicalLocation
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 255
    dpt_sub_number = 1
    value_type = "geographical_location"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> GeographicalLocation:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        value = GeographicalLocation(
            longitude=DPT4ByteFloat.from_knx(DPTArray(raw[:4])),
            latitude=DPT4ByteFloat.from_knx(DPTArray(raw[4:])),
        )
        _check_range(value)
        return value

    @classmethod
    def _to_knx(cls, value: GeographicalLocation) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        _check_range(value)
        return DPTArray(
            (
                *DPT4ByteFloat.to_knx(value.longitude).value,
                *DPT4ByteFloat.to_knx(value.latitude).value,
            )
        )
