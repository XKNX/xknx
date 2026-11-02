"""Implementation of the KNX DALI emergency converter info data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData
from .dpt_7 import DPTTimePeriodHrs
from .dpt_248 import ConverterInfoValid
from .helpers.metadata import RANGE_UINT16
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class ConverterInfo(DPTComplexData):
    """
    Representation of DALI emergency converter information.

    `info_valid`: validity of the converter information
    `lamp_emergency_time`: accumulated lamp operation time on battery power in hours
    `lamp_total_operation_time`: accumulated total lamp operation time in hours
    `emergency_level`: emergency level 0..254; None if unknown
    `short_address`: DALI short address 0..63
    """

    info_valid: ConverterInfoValid
    lamp_emergency_time: int = field(metadata=RANGE_UINT16)
    lamp_total_operation_time: int = field(metadata=RANGE_UINT16)
    emergency_level: int | None = field(metadata={"value_min": 0, "value_max": 254})
    short_address: int = field(metadata={"value_min": 0, "value_max": 63})

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConverterInfo:
        """Init from a dictionary."""
        try:
            info_valid = ConverterInfoValid.parse(data["info_valid"])
            lamp_emergency_time = int(data["lamp_emergency_time"])
            lamp_total_operation_time = int(data["lamp_total_operation_time"])
            emergency_level = data.get("emergency_level")
            if emergency_level is not None:
                emergency_level = int(emergency_level)
            short_address = int(data["short_address"])
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for ConverterInfo: {err}") from err
        return cls(
            info_valid=info_valid,
            lamp_emergency_time=lamp_emergency_time,
            lamp_total_operation_time=lamp_total_operation_time,
            emergency_level=emergency_level,
            short_address=short_address,
        )

    def as_dict(self) -> dict[str, str | int | None]:
        """Create a JSON serializable dictionary."""
        return {
            "info_valid": self.info_valid.name.lower(),
            "lamp_emergency_time": self.lamp_emergency_time,
            "lamp_total_operation_time": self.lamp_total_operation_time,
            "emergency_level": self.emergency_level,
            "short_address": self.short_address,
        }


class DPTConverterInfo(DPTComplex[ConverterInfo]):
    """
    Abstraction for KNX 7 octet DALI converter info (DPT 272.600).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.22
    """

    data_type = ConverterInfo
    payload_type = DPTArray
    payload_length = 7
    dpt_main_number = 272
    dpt_sub_number = 600
    value_type = "converter_info"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ConverterInfo:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        try:
            info_valid = ConverterInfoValid(raw[0])
            if raw[6] > 63:
                raise ValueError(f"Short address out of range 0..63: {raw[6]}")
        except ValueError as err:
            raise ConversionError(
                f"Could not parse {cls.dpt_name()}: {err}", raw=raw
            ) from err
        return ConverterInfo(
            info_valid=info_valid,
            lamp_emergency_time=DPTTimePeriodHrs.from_knx(DPTArray(raw[1:3])),
            lamp_total_operation_time=DPTTimePeriodHrs.from_knx(DPTArray(raw[3:5])),
            emergency_level=raw[5] if raw[5] != 0xFF else None,
            short_address=raw[6],
        )

    @classmethod
    def _to_knx(cls, value: ConverterInfo) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        emergency_level = value.emergency_level
        if emergency_level is None:
            emergency_level = 0xFF
        elif not 0 <= emergency_level <= 254:
            raise ConversionError(
                f"Emergency level out of range 0..254: {emergency_level}"
            )
        if not 0 <= value.short_address <= 63:
            raise ConversionError(
                f"Short address out of range 0..63: {value.short_address}"
            )
        return DPTArray(
            (
                ConverterInfoValid(value.info_valid).value,
                *DPTTimePeriodHrs.to_knx(value.lamp_emergency_time).value,
                *DPTTimePeriodHrs.to_knx(value.lamp_total_operation_time).value,
                emergency_level,
                value.short_address,
            )
        )
