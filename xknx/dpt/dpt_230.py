"""Implementation of the KNX 230 data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar

from ..exceptions import ConversionError
from .dpt import DPTComplex, DPTComplexData
from .dpt_20 import MeteringDeviceType
from .helpers.metadata import RANGE_UINT8, RANGE_UINT16, RANGE_UINT32
from .payload import DPTArray, DPTBinary


def _medium(code: int) -> MeteringDeviceType | int:
    """Return the medium of a code; a code the KNX table does not list as int."""
    try:
        return MeteringDeviceType(code)
    except ValueError:
        return code


def _medium_from_dict(medium: Any) -> MeteringDeviceType | int:
    """Parse a medium given by name or by its code 0..255."""
    if isinstance(medium, bool):
        raise ValueError(f"Invalid medium: {medium!r}")
    if isinstance(medium, int):
        if not 0 <= medium <= 255:
            raise ValueError(f"Medium code out of range 0..255: {medium}")
        return _medium(medium)
    return MeteringDeviceType.parse(medium)


@dataclass(slots=True)
class _MBusAddressSchemaFields:
    """The fields of MBusAddress for its dict schema: `medium` as enum."""

    manufacturer_id: int = field(metadata=RANGE_UINT16)
    identification_number: int = field(metadata=RANGE_UINT32)
    version: int = field(metadata=RANGE_UINT8)
    medium: MeteringDeviceType


@dataclass(slots=True)
class MBusAddress(DPTComplexData):
    """
    Representation of an M-Bus address.

    `manufacturer_id`: int 0..65535 M-Bus manufacturer code
    `identification_number`: int 0..4294967295, manufacturer specific encoding
    `version`: int 0..255 device version, manufacturer specific
    `medium`: MeteringDeviceType (DPT 20.114), or the int code 0..255 of a
        medium the KNX table does not list

    The media are those of KNX v01.03.08 - RF Metering protocol 10.03 -
    §3.1.5.3 Table 1, which has cooling load meter inlet as 0Ah and outlet as
    0Bh. DPT 20.114 and the M-Bus device types of EN 13757-3 have them the other
    way around (0Ah outlet, 0Bh inlet), which is followed. Real meters also send
    EN 13757-3 codes the KNX table does not list; these are kept as int rather
    than rejected.
    """

    manufacturer_id: int = field(metadata=RANGE_UINT16)
    identification_number: int = field(metadata=RANGE_UINT32)
    version: int = field(metadata=RANGE_UINT8)
    medium: MeteringDeviceType | int

    _dict_schema_fields_class: ClassVar[type | None] = _MBusAddressSchemaFields

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MBusAddress:
        """Init from a dictionary."""
        try:
            return cls(
                manufacturer_id=int(data["manufacturer_id"]),
                identification_number=int(data["identification_number"]),
                version=int(data["version"]),
                medium=_medium_from_dict(data["medium"]),
            )
        except KeyError as err:
            raise ValueError(f"Missing required key: {err}") from err
        except (AttributeError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid value for MBusAddress: {err}") from err

    def as_dict(self) -> dict[str, int | str]:
        """Create a JSON serializable dictionary."""
        return {
            "manufacturer_id": self.manufacturer_id,
            "identification_number": self.identification_number,
            "version": self.version,
            "medium": (
                self.medium.name.lower()
                if isinstance(self.medium, MeteringDeviceType)
                else self.medium
            ),
        }


class DPTMBusAddress(DPTComplex[MBusAddress]):
    """
    Abstraction for KNX 8 octet M-Bus address (DPT 230.1000).

    DPT_MBus_Address - KNX v02.02.01 - Datapoint Types 03.07.02 - §8.6
    """

    data_type = MBusAddress
    payload_type = DPTArray
    payload_length = 8
    dpt_main_number = 230
    dpt_sub_number = 1000
    value_type = "mbus_address"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> MBusAddress:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return MBusAddress(
            manufacturer_id=int.from_bytes(raw[0:2], "big"),
            identification_number=int.from_bytes(raw[2:6], "big"),
            version=raw[6],
            medium=_medium(raw[7]),
        )

    @classmethod
    def _to_knx(cls, value: MBusAddress) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        medium = (
            value.medium.value
            if isinstance(value.medium, MeteringDeviceType)
            else value.medium
        )
        if (
            not isinstance(medium, int)
            or isinstance(medium, bool)
            or not 0 <= medium <= 255
        ):
            raise ConversionError(f"Invalid medium for {cls.dpt_name()}", value=value)
        try:
            return DPTArray(
                (
                    *value.manufacturer_id.to_bytes(2, "big"),
                    *value.identification_number.to_bytes(4, "big"),
                    *value.version.to_bytes(1, "big"),
                    medium,
                )
            )
        except OverflowError as err:
            raise ConversionError(
                f"Value out of range for {cls.dpt_name()}: {err}", value=value
            ) from err
