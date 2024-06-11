"""Group address data point type table."""

from __future__ import annotations

from collections.abc import Mapping
import logging

from xknx.dpt.dpt import DPTBase, _DPTMainSubDict
from xknx.exceptions import CouldNotParseAddress
from xknx.telegram.address import (
    DeviceAddressableType,
    DeviceGroupAddress,
    parse_device_group_address,
)

_GA_DPT_LOGGER = logging.getLogger("xknx.ga_dpt")


class GroupAddressDPT:
    """Class for mapping group addresses to data point types for eager decoding."""

    __slots__ = ("_ga_dpts",)

    def __init__(self) -> None:
        """Initialize GADataTypes class."""
        # using dict[int | str] instead of dict[DeviceGroupAddress] is faster.
        self._ga_dpts: dict[int | str, type[DPTBase]] = {}

    def set_dpts(
        self,
        ga_dpt: Mapping[DeviceAddressableType, int | str | _DPTMainSubDict],
    ) -> None:
        """Assign decoders to group addresses."""
        unknown_dpts = set()
        for addr, dpt in ga_dpt.items():
            try:
                address = parse_device_group_address(addr)
            except CouldNotParseAddress as err:
                _GA_DPT_LOGGER.warning("Invalid group address %s: %s", addr, err)
                continue
            if (transcoder := DPTBase.parse_transcoder(dpt)) is None:
                unknown_dpts.add(repr(dpt))  # prevent unhashable types (dict)
                continue
            self._ga_dpts[address.raw] = transcoder  # type: ignore[type-abstract]
        if unknown_dpts:
            _GA_DPT_LOGGER.debug("No transcoder found for DPTs: %s", unknown_dpts)

    def get_transcoder(self, address: DeviceGroupAddress) -> type[DPTBase] | None:
        """Return transcoder for group address."""
        return self._ga_dpts.get(address.raw)
