"""Implementation of the KNX 230 data point type."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ..exceptions import ConversionError
from .dpt import DPTComplex, DPTComplexData, DPTEnumData
from .helpers.metadata import RANGE_UINT8, RANGE_UINT16
from .payload import DPTArray, DPTBinary

_RANGE_UINT32 = {"value_min": 0, "value_max": 4_294_967_295}


class MBusMedium(DPTEnumData):
    """
    Measured medium (device type) of an M-Bus meter.

    Encoding according to EN 13757-3, limited to the media supported by KNX:
    KNX v01.03.08 - RF Metering protocol 10.03 - §3.1.5.3 Table 1. Named like
    DPT_Metering_DeviceType (20.114), which uses the same codes.
    """

    OTHER = 0x00
    OIL_METER = 0x01
    ELECTRICITY_METER = 0x02
    GAS_METER = 0x03
    HEAT_METER = 0x04
    STEAM_METER = 0x05
    WARM_WATER_METER = 0x06
    WATER_METER = 0x07
    HEAT_COST_ALLOCATOR = 0x08
    COOLING_LOAD_METER_OUTLET = 0x0A
    COOLING_LOAD_METER_INLET = 0x0B
    HEAT_INLET = 0x0C
    HEAT_AND_COOL = 0x0D
    BREAKER = 0x20
    VALVE = 0x21
    WASTE_WATER_METER = 0x28
    GARBAGE = 0x29


@dataclass(slots=True)
class MBusAddress(DPTComplexData):
    """
    Representation of an M-Bus address.

    `manufacturer_id`: int 0..65535 M-Bus manufacturer code
    `identification_number`: int 0..4294967295, manufacturer specific encoding
    `version`: int 0..255 device version, manufacturer specific
    `medium`: MBusMedium
    """

    manufacturer_id: int = field(metadata=RANGE_UINT16)
    identification_number: int = field(metadata=_RANGE_UINT32)
    version: int = field(metadata=RANGE_UINT8)
    medium: MBusMedium

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MBusAddress:
        """Init from a dictionary."""
        try:
            return cls(
                manufacturer_id=int(data["manufacturer_id"]),
                identification_number=int(data["identification_number"]),
                version=int(data["version"]),
                medium=MBusMedium.parse(data["medium"]),
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
            "medium": self.medium.name.lower(),
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
        try:
            medium = MBusMedium(raw[7])
        except ValueError:
            raise ConversionError(
                f"Payload not supported for {cls.dpt_name()}", raw=raw
            ) from None
        return MBusAddress(
            manufacturer_id=int.from_bytes(raw[0:2], "big"),
            identification_number=int.from_bytes(raw[2:6], "big"),
            version=raw[6],
            medium=medium,
        )

    @classmethod
    def _to_knx(cls, value: MBusAddress) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        if not isinstance(value.medium, MBusMedium):
            raise ConversionError(f"Invalid medium for {cls.dpt_name()}", value=value)
        try:
            return DPTArray(
                (
                    *value.manufacturer_id.to_bytes(2, "big"),
                    *value.identification_number.to_bytes(4, "big"),
                    *value.version.to_bytes(1, "big"),
                    value.medium.value,
                )
            )
        except OverflowError as err:
            raise ConversionError(
                f"Value out of range for {cls.dpt_name()}: {err}", value=value
            ) from err
