"""Group address data point type table."""

from __future__ import annotations

from collections.abc import Mapping
import logging

from xknx.dpt.dpt import DPTBase
from xknx.exceptions import ConversionError, CouldNotParseAddress, CouldNotParseTelegram
from xknx.telegram import Telegram, TelegramDecodedData
from xknx.telegram.address import (
    DeviceAddressableType,
    DeviceGroupAddress,
    GroupAddress,
    InternalGroupAddress,
    parse_device_group_address,
)
from xknx.telegram.apci import GroupValueResponse, GroupValueWrite
from xknx.typing import DPTParsable

_GA_DPT_LOGGER = logging.getLogger("xknx.ga_dpt")


class GroupAddressDPT:
    """Class for mapping group addresses to data point types for eager decoding."""

    __slots__ = ("_ga_dpts", "ga_decoding_error")

    def __init__(self) -> None:
        """Initialize GADataTypes class."""
        # using dict[int | str] instead of dict[DeviceGroupAddress] is faster.
        self._ga_dpts: dict[int | str, type[DPTBase]] = {}
        self.ga_decoding_error: set[GroupAddress | InternalGroupAddress] = set()

    def set(
        self,
        ga_dpt: Mapping[DeviceAddressableType, DPTParsable],
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
            self._ga_dpts[address.raw] = transcoder
        if unknown_dpts:
            _GA_DPT_LOGGER.debug("No transcoder found for DPTs: %s", unknown_dpts)

    def get(self, address: DeviceGroupAddress) -> type[DPTBase] | None:
        """Return transcoder for group address."""
        return self._ga_dpts.get(address.raw)

    def clear(self) -> None:
        """Clear all group addresses."""
        self._ga_dpts = {}

    def set_decoded_data(self, telegram: Telegram) -> None:
        """Update telegram data with decoded value."""
        if telegram.decoded_data is not None:
            return
        if not isinstance(telegram.payload, GroupValueWrite | GroupValueResponse):
            return
        assert isinstance(  # GroupValueWrite and GroupValueResponse can not have IndividualAddress
            telegram.destination_address, GroupAddress | InternalGroupAddress
        )
        if (transcoder := self.get(telegram.destination_address)) is None:
            return
        try:
            value = transcoder.from_knx(telegram.payload.value)
        except (CouldNotParseTelegram, ConversionError) as err:
            if telegram.destination_address in self.ga_decoding_error:
                _logger_fn = _GA_DPT_LOGGER.debug
            else:
                _logger_fn = _GA_DPT_LOGGER.warning
            self.ga_decoding_error.add(telegram.destination_address)
            _logger_fn(
                "DPT decoding error. Telegram from %s to %s with payload %s can't be decoded by %s: %s",
                telegram.source_address,
                telegram.destination_address,
                telegram.payload.value,
                transcoder.dpt_name(),
                err,
            )
            return
        telegram.decoded_data = TelegramDecodedData(transcoder, value)
