"""Implementation of KNX DPT 30 24-bit sets."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from .dpt import DPTComplex
from .helpers.bitset import _BitsetData
from .payload import DPTArray, DPTBinary


@dataclass(slots=True)
class ChannelActivation24(_BitsetData):
    """
    Representation of the activation state of 24 channels.

    `channel_<n>`: True if the visual effect of channel n is active.
    Channel n is bit n-1.

    KNX v02.02.01 - Datapoint Types 03.07.02 - §8.5.1
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
    channel_17: bool = False
    channel_18: bool = False
    channel_19: bool = False
    channel_20: bool = False
    channel_21: bool = False
    channel_22: bool = False
    channel_23: bool = False
    channel_24: bool = False

    _bits: ClassVar[Mapping[str, int]] = {
        f"channel_{bit + 1}": bit for bit in range(24)
    }


class DPTChannelActivation24(DPTComplex[ChannelActivation24]):
    """Abstraction for KNX 3 octet channel activation for 24 channels (DPT 30.1010)."""

    data_type = ChannelActivation24
    payload_type = DPTArray
    payload_length = 3
    dpt_main_number = 30
    dpt_sub_number = 1010
    value_type = "channel_activation_24"

    @classmethod
    def from_knx(cls, payload: DPTArray | DPTBinary) -> ChannelActivation24:
        """Parse/deserialize from KNX/IP raw data."""
        raw = cls.validate_payload(payload)
        return ChannelActivation24.from_raw(raw[0] << 16 | raw[1] << 8 | raw[2])

    @classmethod
    def _to_knx(cls, value: ChannelActivation24) -> DPTArray:
        """Serialize to KNX/IP raw data."""
        raw = value.to_raw()
        return DPTArray((raw >> 16 & 0xFF, raw >> 8 & 0xFF, raw & 0xFF))
