"""Implementation of the KNX DALI emergency converter info fix data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData, DPTEnumData
from .helpers.metadata import RANGE_UINT8
from .payload import DPTArray, DPTBinary

_GEAR_FEATURES = (
    "integral_emergency_control_gear",
    "maintained_control_gear",
    "switched_maintained_control_gear",
    "auto_test_capability",
    "adjustable_emergency_level",
    "hardwired_inhibit_supported",
    "physical_selection_supported",
    "relight_in_rest_mode_supported",
)


class ConverterInfoValid(DPTEnumData):
    """Validity of the converter information."""

    NOT_AVAILABLE = 0  # converter not existing or no information available
    VALID = 1
    INVALID = 2  # e.g. not a type 1 device


@dataclass(slots=True)
class ConverterInfoFix(DPTComplexData):
    """
    Representation of fixed DALI emergency converter information.

    `info_valid`: validity of the converter information
    `emergency_min_level`: minimum brightness level in emergency mode 0..254;
        None if unknown
    `emergency_max_level`: maximum brightness level in emergency mode 0..254;
        None if unknown
    `rated_duration`: rated duration of the emergency light in minutes 0..255
    `integral_emergency_control_gear` .. `relight_in_rest_mode_supported`:
        gear features
    """

    info_valid: ConverterInfoValid
    emergency_min_level: int | None = field(metadata={"value_min": 0, "value_max": 254})
    emergency_max_level: int | None = field(metadata={"value_min": 0, "value_max": 254})
    rated_duration: int = field(metadata=RANGE_UINT8)
    integral_emergency_control_gear: bool
    maintained_control_gear: bool
    switched_maintained_control_gear: bool
    auto_test_capability: bool
    adjustable_emergency_level: bool
    hardwired_inhibit_supported: bool
    physical_selection_supported: bool
    relight_in_rest_mode_supported: bool

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConverterInfoFix:
        """Init from a dictionary."""
        try:
            info_valid = ConverterInfoValid.parse(data["info_valid"])
            min_level = data.get("emergency_min_level")
            max_level = data.get("emergency_max_level")
            if min_level is not None:
                min_level = int(min_level)
            if max_level is not None:
                max_level = int(max_level)
            rated_duration = int(data["rated_duration"])
            features = [data[name] for name in _GEAR_FEATURES]
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for ConverterInfoFix: {err}") from err
        for name, feature in zip(_GEAR_FEATURES, features, strict=True):
            if not isinstance(feature, bool):
                raise ValueError(
                    f"Invalid value for ConverterInfoFix value `{name}`: {feature}"
                )
        return cls(info_valid, min_level, max_level, rated_duration, *features)

    def as_dict(self) -> dict[str, str | int | bool | None]:
        """Create a JSON serializable dictionary."""
        return {
            "info_valid": self.info_valid.name.lower(),
            "emergency_min_level": self.emergency_min_level,
            "emergency_max_level": self.emergency_max_level,
            "rated_duration": self.rated_duration,
            **{name: getattr(self, name) for name in _GEAR_FEATURES},
        }


def _encode_level(level: int | None) -> int:
    """Encode an emergency level; None (unknown) is sent as 255."""
    if level is None:
        return 0xFF
    if not 0 <= level <= 254:
        raise ValueError(f"Level out of range 0..254: {level}")
    return level


class DPTConverterInfoFix(DPTComplex[ConverterInfoFix]):
    """
    Abstraction for KNX 5 octet DALI converter info fix (DPT 248.600).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.15
    """

    data_type = ConverterInfoFix
    payload_type = DPTArray
    payload_length = 5
    dpt_main_number = 248
    dpt_sub_number = 600
    value_type = "converter_info_fix"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ConverterInfoFix:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        try:
            info_valid = ConverterInfoValid(raw[0])
        except ValueError as err:
            raise ConversionError(
                f"Could not parse {cls.dpt_name()}: {err}", raw=raw
            ) from err
        return ConverterInfoFix(
            info_valid,
            raw[1] if raw[1] != 0xFF else None,
            raw[2] if raw[2] != 0xFF else None,
            raw[3],
            *(bool(raw[4] >> bit & 0b1) for bit in range(len(_GEAR_FEATURES))),
        )

    @classmethod
    def _to_knx(cls, value: ConverterInfoFix) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not 0 <= value.rated_duration <= 255:
            raise ValueError(
                f"Rated duration out of range 0..255: {value.rated_duration}"
            )
        features = 0
        for bit, name in enumerate(_GEAR_FEATURES):
            features |= bool(getattr(value, name)) << bit
        return DPTArray(
            (
                ConverterInfoValid(value.info_valid).value,
                _encode_level(value.emergency_min_level),
                _encode_level(value.emergency_max_level),
                value.rated_duration,
                features,
            )
        )
