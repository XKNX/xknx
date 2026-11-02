"""Implementation of the KNX 229 data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ..exceptions import ConversionError
from .dpt import DPTComplex, DPTComplexData, DPTEnumData
from .dpt_13 import DPTValue4Count
from .helpers.metadata import RANGE_INT32
from .payload import DPTArray, DPTBinary


class MeteringValueUnit(DPTEnumData):
    """
    Quantity and unit of a metering value.

    Member values are the ValInfField codes with a power of ten exponent
    'nnn' / 'n' of 0.
    """

    ENERGY_WH = 0x00
    ENERGY_J = 0x08
    VOLUME_M3 = 0x10
    MASS_KG = 0x18
    POWER_W = 0x28
    POWER_J_PER_H = 0x30
    VOLUME_FLOW_M3_PER_H = 0x38
    VOLUME_FLOW_M3_PER_MIN = 0x40
    VOLUME_FLOW_M3_PER_S = 0x48
    MASS_FLOW_KG_PER_H = 0x50
    HCA_UNITS = 0x6E
    DIMENSIONLESS_COUNTER = 0xBA


def _build_val_inf_codes() -> dict[int, tuple[MeteringValueUnit, int]]:
    """Return ValInfField code -> (unit, power of ten exponent)."""
    codes: dict[int, tuple[MeteringValueUnit, int]] = {}
    # (unit, first code, exponent of first code, number of codes)
    for unit, first_code, first_exponent, count in (
        # 'nnn' codes - subset of the M-Bus primary VIF table
        (MeteringValueUnit.ENERGY_WH, 0x00, -3, 8),
        (MeteringValueUnit.ENERGY_J, 0x08, 0, 8),
        (MeteringValueUnit.VOLUME_M3, 0x10, -6, 8),
        (MeteringValueUnit.MASS_KG, 0x18, -3, 8),
        (MeteringValueUnit.POWER_W, 0x28, -3, 8),
        (MeteringValueUnit.POWER_J_PER_H, 0x30, 0, 8),
        (MeteringValueUnit.VOLUME_FLOW_M3_PER_H, 0x38, -6, 8),
        (MeteringValueUnit.VOLUME_FLOW_M3_PER_MIN, 0x40, -7, 8),
        (MeteringValueUnit.VOLUME_FLOW_M3_PER_S, 0x48, -9, 8),
        (MeteringValueUnit.MASS_FLOW_KG_PER_H, 0x50, -3, 8),
        # 'n' codes - mapped M-Bus VIFE codes for MWh, GJ, MW and GJ/h
        (MeteringValueUnit.ENERGY_WH, 0x80, 5, 2),
        (MeteringValueUnit.ENERGY_J, 0x88, 8, 2),
        (MeteringValueUnit.POWER_W, 0xA8, 5, 2),
        (MeteringValueUnit.POWER_J_PER_H, 0xB0, 8, 2),
        # dimensionless
        (MeteringValueUnit.HCA_UNITS, 0x6E, 0, 1),
        (MeteringValueUnit.DIMENSIONLESS_COUNTER, 0xBA, 0, 1),
    ):
        for offset in range(count):
            codes[first_code + offset] = (unit, first_exponent + offset)
    return codes


_VAL_INF_CODES = _build_val_inf_codes()
_VAL_INF_FIELDS = {meaning: code for code, meaning in _VAL_INF_CODES.items()}
_STATUS_BITS = ("out_of_service", "fault", "overridden", "in_alarm", "alarm_un_ack")


@dataclass(slots=True)
class MeteringValue(DPTComplexData):
    """
    Representation of a metering value.

    The metered quantity is `counter_value` * 10 ** `exponent` `unit`.

    `counter_value`: int 4byte signed. If `fault` is set (and `overridden` is
        not) it holds failure information instead: 0 general fault,
        1 sensor open circuit, 2 sensor short circuit.
    `unit`: MeteringValueUnit
    `exponent`: int power of ten of `unit`; Wh -3..6, J 0..9, m³ -6..1,
        kg -3..4, W -3..6, J/h 0..9, m³/h -6..1, m³/min -7..0, m³/s -9..-2,
        kg/h -3..4; 0 for the dimensionless units
    `out_of_service`, `fault`, `overridden`, `in_alarm`, `alarm_un_ack`: bool
        STATUS attributes of the Z8 field
    """

    counter_value: int = field(metadata=RANGE_INT32)
    unit: MeteringValueUnit
    exponent: int = field(default=0, metadata={"value_min": -9, "value_max": 9})
    out_of_service: bool = False
    fault: bool = False
    overridden: bool = False
    in_alarm: bool = False
    alarm_un_ack: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MeteringValue:
        """Init from a dictionary."""
        try:
            counter_value = int(data["counter_value"])
            unit = MeteringValueUnit.parse(data["unit"])
            exponent = int(data.get("exponent", 0))
        except KeyError as err:
            raise ValueError(f"Missing required key: {err}") from err
        except (AttributeError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for MeteringValue: {err}") from err
        bits: dict[str, bool] = {}
        for name in _STATUS_BITS:
            bit = data.get(name, False)
            if bit not in (True, False):
                raise ValueError(f"Invalid value for {name}: {bit!r}")
            bits[name] = bool(bit)
        return cls(
            counter_value=counter_value,
            unit=unit,
            exponent=exponent,
            out_of_service=bits["out_of_service"],
            fault=bits["fault"],
            overridden=bits["overridden"],
            in_alarm=bits["in_alarm"],
            alarm_un_ack=bits["alarm_un_ack"],
        )

    def as_dict(self) -> dict[str, int | str | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "counter_value": self.counter_value,
            "unit": self.unit.name.lower(),
            "exponent": self.exponent,
            "out_of_service": self.out_of_service,
            "fault": self.fault,
            "overridden": self.overridden,
            "in_alarm": self.in_alarm,
            "alarm_un_ack": self.alarm_un_ack,
        }


class DPTMeteringValue(DPTComplex[MeteringValue]):
    """
    Abstraction for KNX 6 octet metering value (DPT 229.001).

    DPT_MeteringValue - KNX v02.02.01 - Datapoint Types 03.07.02 - §3.45.1
    The ValInfField is decoded into `unit` and `exponent`. The Z8 field is
    decoded as STATUS (KNX v02.02.01 - Datapoint Types 03.07.02 - §4.1.2);
    its COMMAND interpretation only applies to write services of property
    and LTE access. A COMMAND 'NormalWrite' is all STATUS attributes false.
    """

    data_type = MeteringValue
    payload_type = DPTArray
    payload_length = 6
    dpt_main_number = 229
    dpt_sub_number = 1
    value_type = "metering_value"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> MeteringValue:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        try:
            unit, exponent = _VAL_INF_CODES[raw[4]]
        except KeyError:
            raise ConversionError(
                f"Payload not supported for {cls.dpt_name()}", raw=raw
            ) from None
        status = raw[5]  # reserved bits 5..7 are ignored
        return MeteringValue(
            counter_value=DPTValue4Count.from_knx(DPTArray(raw[:4])),
            unit=unit,
            exponent=exponent,
            out_of_service=bool(status & 0x01),
            fault=bool(status & 0x02),
            overridden=bool(status & 0x04),
            in_alarm=bool(status & 0x08),
            alarm_un_ack=bool(status & 0x10),
        )

    @classmethod
    def _to_knx(cls, value: MeteringValue) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        try:
            val_inf_field = _VAL_INF_FIELDS[(value.unit, value.exponent)]
        except KeyError:
            raise ConversionError(
                f"Exponent {value.exponent} not supported for unit {value.unit} "
                f"in {cls.dpt_name()}",
                value=value,
            ) from None
        status = (
            bool(value.alarm_un_ack) << 4
            | bool(value.in_alarm) << 3
            | bool(value.overridden) << 2
            | bool(value.fault) << 1
            | bool(value.out_of_service)
        )
        return DPTArray(
            (
                *DPTValue4Count.to_knx(value.counter_value).value,
                val_inf_field,
                status,
            )
        )
