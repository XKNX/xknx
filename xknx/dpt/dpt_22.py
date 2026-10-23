"""Implementation of KNX DPT 22 16-bit sets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar

from .dpt import DPTComplex, DPTComplexData
from .dpt_1 import HeatCool
from .helpers.bitset import _BitsetData, bits_from_dict, bits_from_raw, bits_to_raw
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class DHWControllerStatus(_BitsetData):
    """Value of DPT 22.100 DPT_StatusDHWC."""

    fault: bool = False
    dhw_load_active: bool = False
    legio_prot_active: bool = False
    dhw_push_active: bool = False
    other_energy_source_active: bool = False
    solar_energy_only: bool = False
    solar_energy_support: bool = False
    temp_optim_shift_active: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "fault": 0,
        "dhw_load_active": 1,
        "legio_prot_active": 2,
        "dhw_push_active": 3,
        "other_energy_source_active": 4,
        "solar_energy_only": 5,
        "solar_energy_support": 6,
        "temp_optim_shift_active": 7,
    }


class DPTStatusDHWC(DPTComplex[DHWControllerStatus]):
    """
    Abstraction for KNX 2 octet DHW Controller Status (DPT 22.100 DPT_StatusDHWC).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.5.1
    """

    data_type = DHWControllerStatus
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 22
    dpt_sub_number = 100
    value_type = "dhw_controller_status"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> DHWControllerStatus:
        """Parse/deserialize from KNX/IP raw data."""
        return DHWControllerStatus.from_raw(_from_b16(cls.validate_payload(payload)))

    @classmethod
    def _to_knx(cls, value: DHWControllerStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _to_b16(value.to_raw())


_RHCC_BITS: Mapping[str, int] = {
    "fault": 0,
    "status_eco_h": 1,
    "temp_flow_limit": 2,
    "temp_return_limit": 3,
    "status_morning_boost_h": 4,
    "status_start_optim": 5,
    "status_stop_optim": 6,
    "heating_disabled": 7,
    # bit 8 is HeatCoolMode
    "status_eco_c": 9,
    "status_pre_cool": 10,
    "cooling_disabled": 11,
    "dew_point_status": 12,
    "frost_alarm": 13,
    "overheat_alarm": 14,
}
_RHCC_HEAT_COOL_MODE_BIT = 8


@dataclass(slots=True)
class RoomHeatingCoolingControllerStatus(DPTComplexData):
    """
    Value of DPT 22.101 DPT_StatusRHCC.

    `heat_cool_mode`: HeatCool; defaults to heating.
    `dew_point_status`, `frost_alarm`, `overheat_alarm`: True if in alarm.
    All other fields: True if the status is active.
    """

    fault: bool = False
    status_eco_h: bool = False
    temp_flow_limit: bool = False
    temp_return_limit: bool = False
    status_morning_boost_h: bool = False
    status_start_optim: bool = False
    status_stop_optim: bool = False
    heating_disabled: bool = False
    heat_cool_mode: HeatCool = HeatCool.HEAT
    status_eco_c: bool = False
    status_pre_cool: bool = False
    cooling_disabled: bool = False
    dew_point_status: bool = False
    frost_alarm: bool = False
    overheat_alarm: bool = False

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RoomHeatingCoolingControllerStatus:
        """Init from a dictionary. Missing keys take the field default."""
        if not isinstance(data, Mapping):
            raise ValueError(f"Invalid data for {cls.__name__}: {data!r}")
        flags = bits_from_dict(
            {key: value for key, value in data.items() if key != "heat_cool_mode"},
            _RHCC_BITS,
        )
        heat_cool_mode = HeatCool.parse(data.get("heat_cool_mode", HeatCool.HEAT))
        return cls(heat_cool_mode=heat_cool_mode, **flags)

    def as_dict(self) -> dict[str, bool | str]:
        """Create a JSON serializable dictionary."""
        result: dict[str, bool | str] = {
            name: getattr(self, name) for name in _RHCC_BITS
        }
        result["heat_cool_mode"] = self.heat_cool_mode.name.lower()
        return result


class DPTStatusRHCC(DPTComplex[RoomHeatingCoolingControllerStatus]):
    """
    Abstraction for KNX 2 octet Room Heating/Cooling Controller Status (DPT 22.101 DPT_StatusRHCC).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.5.2
    """

    data_type = RoomHeatingCoolingControllerStatus
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 22
    dpt_sub_number = 101
    value_type = "room_heating_cooling_controller_status"

    @classmethod
    def from_knx(
        cls, payload: DPTArray | DPTBinary
    ) -> RoomHeatingCoolingControllerStatus:
        """Parse/deserialize from KNX/IP raw data."""
        raw = _from_b16(cls.validate_payload(payload))
        return RoomHeatingCoolingControllerStatus(
            heat_cool_mode=HeatCool(bool(raw >> _RHCC_HEAT_COOL_MODE_BIT & 1)),
            **bits_from_raw(raw, _RHCC_BITS),
        )

    @classmethod
    def _to_knx(cls, value: RoomHeatingCoolingControllerStatus) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        heat_cool_mode = HeatCool.parse(value.heat_cool_mode)
        return _to_b16(
            bits_to_raw(value, _RHCC_BITS)
            | heat_cool_mode.value << _RHCC_HEAT_COOL_MODE_BIT
        )


@dataclass(slots=True)
class SupportedMedia(_BitsetData):
    """Value of DPT 22.1000 DPT_Media: the KNX media a device supports."""

    tp1: bool = False
    pl110: bool = False
    rf: bool = False
    knx_ip: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        "tp1": 1,
        "pl110": 2,
        "rf": 4,
        "knx_ip": 5,
    }


class DPTMedia(DPTComplex[SupportedMedia]):
    """
    Abstraction for KNX 2 octet Media (DPT 22.1000 DPT_Media).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.3.1
    """

    data_type = SupportedMedia
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 22
    dpt_sub_number = 1000
    value_type = "supported_media"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> SupportedMedia:
        """Parse/deserialize from KNX/IP raw data."""
        return SupportedMedia.from_raw(_from_b16(cls.validate_payload(payload)))

    @classmethod
    def _to_knx(cls, value: SupportedMedia) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _to_b16(value.to_raw())


@dataclass(slots=True)
class ChannelActivation16(_BitsetData):
    """
    Value of DPT 22.1010 DPT_Channel_Activation_16.

    `channel_<n>`: True if the visual effect of channel n is active.
    Bit n is channel n+1, as the spec says. The master data (DPST-22-1010) lists
    channel 1 as the most significant bit instead, i.e. the opposite order; the
    spec is followed.
    """

    channel_1: bool = False
    channel_2: bool = False
    channel_3: bool = False
    channel_4: bool = False
    channel_5: bool = False
    channel_6: bool = False
    channel_7: bool = False
    channel_8: bool = False
    channel_9: bool = False
    channel_10: bool = False
    channel_11: bool = False
    channel_12: bool = False
    channel_13: bool = False
    channel_14: bool = False
    channel_15: bool = False
    channel_16: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        f"channel_{bit + 1}": bit for bit in range(16)
    }


class DPTChannelActivation16(DPTComplex[ChannelActivation16]):
    """
    Abstraction for KNX 2 octet Channel Activation for 16 channels (DPT 22.1010).

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.3.2
    """

    data_type = ChannelActivation16
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 22
    dpt_sub_number = 1010
    value_type = "channel_activation_16"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ChannelActivation16:
        """Parse/deserialize from KNX/IP raw data."""
        return ChannelActivation16.from_raw(_from_b16(cls.validate_payload(payload)))

    @classmethod
    def _to_knx(cls, value: ChannelActivation16) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _to_b16(value.to_raw())


def _from_b16(raw: tuple[int, ...]) -> int:
    """Join two octets (MSB first) to an integer."""
    return raw[0] << 8 | raw[1]


def _to_b16(raw: int) -> DPTArray:
    """Split an integer into two octets (MSB first)."""
    return DPTArray((raw >> 8 & 0xFF, raw & 0xFF))
