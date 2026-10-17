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
class StatusDHWC(_BitsetData):
    """
    Representation of a DHW controller status.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.5.1
    """

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


class DPTStatusDHWC(DPTComplex[StatusDHWC]):
    """Abstraction for KNX 2 octet DHW controller status (DPT 22.100)."""

    data_type = StatusDHWC
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 22
    dpt_sub_number = 100
    value_type = "status_dhwc"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> StatusDHWC:
        """Parse/deserialize from KNX/IP raw data."""
        return StatusDHWC.from_raw(_from_b16(cls.validate_payload(payload)))

    @classmethod
    def _to_knx(cls, value: StatusDHWC) -> DPTArray:
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
class StatusRHCC(DPTComplexData):
    """
    Representation of a room heating / cooling controller status.

    `heat_cool_mode`: HeatCool; defaults to heating.
    `dew_point_status`, `frost_alarm`, `overheat_alarm`: True if in alarm.
    All other fields: True if the status is active.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §4.5.2
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
    def from_dict(cls, data: Mapping[str, Any]) -> StatusRHCC:
        """Init from a dictionary."""
        flags = bits_from_dict(data, _RHCC_BITS)
        heat_cool_mode = HeatCool.parse(data.get("heat_cool_mode", HeatCool.HEAT))
        return cls(heat_cool_mode=heat_cool_mode, **flags)

    def as_dict(self) -> dict[str, bool | str]:
        """Create a JSON serializable dictionary."""
        result: dict[str, bool | str] = {
            name: getattr(self, name) for name in _RHCC_BITS
        }
        result["heat_cool_mode"] = self.heat_cool_mode.name.lower()
        return result


class DPTStatusRHCC(DPTComplex[StatusRHCC]):
    """Abstraction for KNX 2 octet room heating / cooling controller status (DPT 22.101)."""

    data_type = StatusRHCC
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 22
    dpt_sub_number = 101
    value_type = "status_rhcc"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> StatusRHCC:
        """Parse/deserialize from KNX/IP raw data."""
        raw = _from_b16(cls.validate_payload(payload))
        return StatusRHCC(
            heat_cool_mode=HeatCool(bool(raw >> _RHCC_HEAT_COOL_MODE_BIT & 1)),
            **bits_from_raw(raw, _RHCC_BITS),
        )

    @classmethod
    def _to_knx(cls, value: StatusRHCC) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        heat_cool_mode = HeatCool.parse(value.heat_cool_mode)
        return _to_b16(
            bits_to_raw(value, _RHCC_BITS)
            | heat_cool_mode.value << _RHCC_HEAT_COOL_MODE_BIT
        )


@dataclass(slots=True)
class Media(_BitsetData):
    """
    Representation of supported KNX media.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.3.1
    """

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


class DPTMedia(DPTComplex[Media]):
    """Abstraction for KNX 2 octet supported media (DPT 22.1000)."""

    data_type = Media
    payload_type = DPTArray
    payload_length = 2
    dpt_main_number = 22
    dpt_sub_number = 1000
    value_type = "media"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> Media:
        """Parse/deserialize from KNX/IP raw data."""
        return Media.from_raw(_from_b16(cls.validate_payload(payload)))

    @classmethod
    def _to_knx(cls, value: Media) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        return _to_b16(value.to_raw())


@dataclass(slots=True)
class ChannelActivation16(_BitsetData):
    """
    Representation of the activation state of 16 channels.

    `channel_<n>`: True if the visual effect of channel n is active.
    Channel n is bit n-1.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.3.2
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
    """Abstraction for KNX 2 octet channel activation for 16 channels (DPT 22.1010)."""

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
