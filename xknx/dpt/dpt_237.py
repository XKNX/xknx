"""Implementation of KNX DPT 237 DALI Control Gear Diagnostic."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from xknx.exceptions import ConversionError

from .dpt import DPTComplex, DPTComplexData, DPTEnumData
from .payload import DPTArray, DPTBinary


class DALIAddressIndicator(DPTEnumData):
    """Kind of the DALI address in a DALI Control Gear Diagnostic."""

    DEVICE = 0
    GROUP = 1


_BOOL_FIELDS = ("read_request", "lamp_failure", "ballast_failure", "converter_error")


@dataclass(slots=True)
class DALIControlGearDiagnostic(DPTComplexData):
    """
    Representation of a DALI Control Gear Diagnostic.

    `address`: int; DALI Device Address 0..63 or DALI Group Address 0..15
    `address_indicator`: DALIAddressIndicator; kind of `address`
    `read_request`: bool; True for a read request, False for a response or spontaneous sending
    `lamp_failure`: bool
    `ballast_failure`: bool
    `converter_error`: bool
    """

    address: int = field(metadata={"value_min": 0, "value_max": 63})
    address_indicator: DALIAddressIndicator = DALIAddressIndicator.DEVICE
    read_request: bool = False
    lamp_failure: bool = False
    ballast_failure: bool = False
    converter_error: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DALIControlGearDiagnostic:
        """Init from a dictionary."""
        try:
            address = int(data["address"])
            address_indicator = DALIAddressIndicator.parse(
                data.get("address_indicator", DALIAddressIndicator.DEVICE)
            )
            flags = {key: data.get(key, False) for key in _BOOL_FIELDS}
        except (KeyError, TypeError, ValueError, AttributeError) as err:
            raise ValueError(
                f"Invalid value for DALIControlGearDiagnostic: {err}"
            ) from err
        for key, flag in flags.items():
            if flag not in (True, False):
                raise ValueError(
                    f"Invalid value for DALIControlGearDiagnostic value `{key}`: {flag}"
                )
        return cls(
            address=address,
            address_indicator=address_indicator,
            **{key: bool(flag) for key, flag in flags.items()},
        )

    def as_dict(self) -> dict[str, int | str | bool]:
        """Create a JSON serializable dictionary."""
        return {
            "address": self.address,
            "address_indicator": self.address_indicator.name.lower(),
            "read_request": self.read_request,
            "lamp_failure": self.lamp_failure,
            "ballast_failure": self.ballast_failure,
            "converter_error": self.converter_error,
        }


def _address_max(address_indicator: DALIAddressIndicator) -> int:
    """Return the highest address for the given address kind."""
    return 15 if address_indicator is DALIAddressIndicator.GROUP else 63


class DPTDALIControlGearDiagnostic(DPTComplex[DALIControlGearDiagnostic]):
    """
    Abstraction for KNX 2 Octet DALI Control Gear Diagnostic.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §6.7.1
    DPT 237.600
    """

    data_type = DALIControlGearDiagnostic
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 237
    dpt_sub_number = 600
    value_type = "dali_control_gear_diagnostic"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> DALIControlGearDiagnostic:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        address_indicator = DALIAddressIndicator(raw[1] >> 6 & 0b1)
        address = raw[1] & 0x3F
        if address > _address_max(address_indicator):
            raise ConversionError(f"Could not parse {cls.dpt_name()}", raw=raw)
        # bits 11..15 are reserved and ignored
        return DALIControlGearDiagnostic(
            address=address,
            address_indicator=address_indicator,
            read_request=bool(raw[1] & 0x80),
            lamp_failure=bool(raw[0] & 0x01),
            ballast_failure=bool(raw[0] & 0x02),
            converter_error=bool(raw[0] & 0x04),
        )

    @classmethod
    def _to_knx(cls, value: DALIControlGearDiagnostic) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        address_indicator = DALIAddressIndicator.parse(value.address_indicator)
        address_max = _address_max(address_indicator)
        if not 0 <= value.address <= address_max:
            raise ConversionError(
                f"Address out of range 0..{address_max}: {value.address}"
            )
        return DPTArray(
            (
                bool(value.converter_error) << 2
                | bool(value.ballast_failure) << 1
                | bool(value.lamp_failure),
                bool(value.read_request) << 7
                | address_indicator.value << 6
                | value.address,
            )
        )
