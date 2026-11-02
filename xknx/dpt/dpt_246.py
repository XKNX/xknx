"""Implementation of the KNX DALI emergency battery info data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ..exceptions import ConversionError
from .dpt import DPTComplex, DPTComplexData
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class BatteryInfo(DPTComplexData):
    """
    Representation of DALI emergency battery info.

    `battery_failure`: battery failure
    `battery_duration_failure`: battery duration failure
    `battery_fully_charged`: battery is fully charged
    `charge_level`: recent battery charge level 0 (deep discharge point)..254
        (fully charged); None if unknown or not supported
    """

    battery_failure: bool
    battery_duration_failure: bool
    battery_fully_charged: bool
    charge_level: int | None = field(metadata={"value_min": 0, "value_max": 254})

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BatteryInfo:
        """Init from a dictionary."""
        try:
            battery_failure = data["battery_failure"]
            battery_duration_failure = data["battery_duration_failure"]
            battery_fully_charged = data["battery_fully_charged"]
            charge_level = data.get("charge_level")
            if charge_level is not None:
                charge_level = int(charge_level)
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for BatteryInfo: {err}") from err
        if (
            battery_failure not in (True, False)
            or battery_duration_failure not in (True, False)
            or battery_fully_charged not in (True, False)
        ):
            raise ValueError(
                "Invalid value for BatteryInfo boolean fields: "
                f"{battery_failure=}, {battery_duration_failure=}, "
                f"{battery_fully_charged=}"
            )
        return cls(
            battery_failure=bool(battery_failure),
            battery_duration_failure=bool(battery_duration_failure),
            battery_fully_charged=bool(battery_fully_charged),
            charge_level=charge_level,
        )

    def as_dict(self) -> dict[str, bool | int | None]:
        """Create a JSON serializable dictionary."""
        return {
            "battery_failure": self.battery_failure,
            "battery_duration_failure": self.battery_duration_failure,
            "battery_fully_charged": self.battery_fully_charged,
            "charge_level": self.charge_level,
        }


class DPTBatteryInfo(DPTComplex[BatteryInfo]):
    """
    Abstraction for KNX 2 octet DALI battery info (DPT 246.600).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.13
    """

    data_type = BatteryInfo
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 246
    dpt_sub_number = 600
    value_type = "battery_info"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> BatteryInfo:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return BatteryInfo(
            battery_failure=bool(raw[0] & 0b1),
            battery_duration_failure=bool(raw[0] >> 1 & 0b1),
            battery_fully_charged=bool(raw[0] >> 2 & 0b1),
            charge_level=raw[1] if raw[1] != 0xFF else None,
        )

    @classmethod
    def _to_knx(cls, value: BatteryInfo) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        charge_level = value.charge_level
        if charge_level is None:
            charge_level = 0xFF
        elif not 0 <= charge_level <= 254:
            raise ConversionError(f"Charge level out of range 0..254: {charge_level}")
        return DPTArray(
            (
                bool(value.battery_fully_charged) << 2
                | bool(value.battery_duration_failure) << 1
                | bool(value.battery_failure),
                charge_level,
            )
        )
