"""
Module for managing a remote value on the KNX bus.

Remote value can be :
- a group address for writing a KNX value,
- a group address for reading a KNX value,
- or a group of both representing the same value.
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Callable, Iterator
import logging
from typing import TYPE_CHECKING, Generic, TypeVar, Union

from xknx.dpt import DPTArray, DPTBase, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.address import (
    DeviceGroupAddress,
    InternalGroupAddress,
    parse_device_group_address,
)
from xknx.telegram.apci import GroupValueResponse, GroupValueWrite

if TYPE_CHECKING:
    from xknx.telegram.address import DeviceAddressableType
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")

GroupAddressesType = Union[
    "DeviceAddressableType", list[Union["DeviceAddressableType", None]], None
]
ValueT = TypeVar("ValueT")

RVCallbackType = Callable[[ValueT], None]


class RemoteValue(ABC, Generic[ValueT]):
    """Class for managing remote knx value."""

    dpt_class: type[DPTBase] | None = None

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        sync_state: None | bool | int | float | str = None,
        device_name: str | None = None,
        feature_name: str | None = None,
        after_update_cb: RVCallbackType[ValueT] | None = None,
    ) -> None:
        """Initialize RemoteValue class."""
        self.xknx: XKNX = xknx
        self.passive_group_addresses: list[DeviceGroupAddress] = []

        def unpack_group_addresses(
            addresses: GroupAddressesType,
        ) -> DeviceGroupAddress | None:
            """Parse group addresses and assign passive addresses when given."""
            if addresses is None:
                return None
            if not isinstance(addresses, list):
                return parse_device_group_address(addresses)
            if not addresses:  # empty list
                return None
            active = addresses[0]
            passive = [
                parse_device_group_address(addr)
                for addr in addresses[1:]
                if addr is not None
            ]
            self.passive_group_addresses.extend(passive)
            return parse_device_group_address(active) if active is not None else None

        self.group_address = unpack_group_addresses(group_address)
        self.group_address_state = unpack_group_addresses(group_address_state)

        self.device_name: str = "Unknown" if device_name is None else device_name
        self.feature_name: str = "Unknown" if feature_name is None else feature_name
        self._value: ValueT | None = None
        self.telegram: Telegram | None = None
        self.after_update_cb: RVCallbackType[ValueT] | None = after_update_cb
        self._sync_state = sync_state

    def group_addresses(self) -> Iterator[DeviceGroupAddress]:
        """Return all configured group addresses of this RemoteValue."""
        if self.group_address is not None:
            yield self.group_address
        if self.group_address_state is not None:
            yield self.group_address_state
        yield from self.passive_group_addresses

    def register_state_updater(self) -> None:
        """Register RemoteValue for state updates."""
        sync_state = (
            self._sync_state
            if self._sync_state is not None
            else self.xknx.state_updater.default_use_updater
        )
        if sync_state and self.group_address_state:
            self.xknx.state_updater.register_remote_value(
                self, tracker_options=sync_state
            )

    def unregister_state_updater(self) -> None:
        """Unregister RemoteValue from state updates."""
        try:
            self.xknx.state_updater.unregister_remote_value(self)
        except KeyError:
            # KeyError if it was never added to StateUpdater
            pass

    @property
    def value(self) -> ValueT | None:
        """Get current value."""
        return self._value

    @value.setter
    def value(self, value: ValueT | None) -> None:
        """Set new value without creating a Telegram or calling after_update_cb. Raises ConversionError on invalid value."""
        if value is not None:
            # raises ConversionError on invalid value
            self.to_knx(value)
        self._value = value

    def update_value(self, value: ValueT) -> None:
        """Set new value without creating a Telegram. Calls after_update_cb. Raises ConversionError on invalid value."""
        self.value = value
        if self.after_update_cb is not None:
            self.after_update_cb(value)

    @property
    def initialized(self) -> bool:
        """Evaluate if remote value is initialized with group address."""
        return bool(
            self.group_address_state
            or self.group_address
            or self.passive_group_addresses
        )

    @property
    def readable(self) -> bool:
        """Evaluate if remote value should be read from bus."""
        return bool(self.group_address_state)

    @property
    def writable(self) -> bool:
        """Evaluate if remote value has a group_address set."""
        return bool(self.group_address)

    def from_knx(self, payload: DPTArray | DPTBinary) -> ValueT:
        """Convert current payload to value - to be implemented in derived class when `dpt_class` can't be used."""
        if self.dpt_class is None:
            raise NotImplementedError(
                "Either `dpt_class` must be set or `from_knx` must be implemented"
            )
        return self.dpt_class.from_knx(payload)  # type: ignore[no-any-return]

    def to_knx(self, value: ValueT) -> DPTArray | DPTBinary:
        """Convert value to payload - to be implemented in derived class when `dpt_class` can't be used."""
        if self.dpt_class is None:
            raise NotImplementedError(
                "Either `dpt_class` must be set or `to_knx` must be implemented"
            )
        return self.dpt_class.to_knx(value)

    def process(self, telegram: Telegram, always_callback: bool = False) -> bool:
        """Process incoming or outgoing telegram."""
        if (
            not isinstance(
                telegram.destination_address, GroupAddress | InternalGroupAddress
            )
            or telegram.destination_address not in self.group_addresses()
        ):
            return False
        if not isinstance(telegram.payload, GroupValueWrite | GroupValueResponse):
            raise CouldNotParseTelegram(
                "payload not a GroupValueWrite or GroupValueResponse",
                payload=str(telegram.payload),
                destination_address=str(telegram.destination_address),
                source_address=str(telegram.source_address),
                device_name=self.device_name,
                feature_name=self.feature_name,
            )

        try:
            decoded_payload: ValueT
            if (
                telegram.decoded_data is not None
                and telegram.decoded_data.transcoder is self.dpt_class
            ):
                decoded_payload = telegram.decoded_data.value  # type: ignore[assignment]
            else:
                decoded_payload = self.from_knx(telegram.payload.value)
        except (ConversionError, CouldNotParseTelegram) as err:
            logger.warning(
                "Can not process %s for %s - %s: %s",
                telegram,
                self.device_name,
                self.feature_name,
                err,
            )
            return False
        self.xknx.state_updater.update_received(self)
        if self._value is None or always_callback or self._value != decoded_payload:
            self._value = decoded_payload
            self.telegram = telegram
            if self.after_update_cb is not None:
                self.after_update_cb(decoded_payload)
        return True

    def _send(self, payload: DPTArray | DPTBinary, response: bool = False) -> None:
        """Send payload as telegram to KNX bus."""
        if self.group_address is None:
            return
        telegram = Telegram(
            destination_address=self.group_address,
            payload=(
                GroupValueResponse(payload) if response else GroupValueWrite(payload)
            ),
            source_address=self.xknx.current_address,
        )
        self.xknx.telegrams.put_nowait(telegram)

    def set(self, value: ValueT, response: bool = False) -> None:
        """Set new value."""
        if not self.initialized:
            logger.info(
                "Setting value of uninitialized device: %s - %s (value: %s)",
                self.device_name,
                self.feature_name,
                value,
            )
            return
        if not self.writable:
            logger.warning(
                "Attempted to set value for non-writable device: %s - %s (value: %s)",
                self.device_name,
                self.feature_name,
                value,
            )
            return
        payload = self.to_knx(value)
        self._send(payload, response)
        # self._value is set and after_update_cb() called when the outgoing telegram is processed.

    def respond(self) -> None:
        """Send current payload as GroupValueResponse telegram to KNX bus."""
        if self._value is None:
            return
        payload = self.to_knx(self._value)
        self._send(payload, response=True)

    async def read_state(self, wait_for_result: bool = False) -> None:
        """Send GroupValueRead telegram for state address to KNX bus."""
        if self.group_address_state is not None:
            # pylint: disable=import-outside-toplevel
            # TODO: send a ReadRequest and start a timeout from here instead of ValueReader
            #       cancel timeout form process(); delete ValueReader
            from xknx.core import ValueReader

            value_reader = ValueReader(self.xknx, self.group_address_state)
            if wait_for_result:
                if await value_reader.read() is None:
                    logger.warning(
                        "Could not sync group address '%s' (%s - %s)",
                        self.group_address_state,
                        self.device_name,
                        self.feature_name,
                    )
            else:
                value_reader.send_group_read()

    @property
    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return None

    def group_addr_str(self) -> str:
        """Return object as readable string."""
        return (
            f"<{self.group_address}, "
            f"{self.group_address_state}, "
            f"{list(map(str, self.passive_group_addresses))}, "
            f"{self.value!r} />"
        )

    def __str__(self) -> str:
        """Return object as string representation."""
        return (
            f"<{self.__class__.__name__} "
            f'device_name="{self.device_name}" '
            f'feature_name="{self.feature_name}" '
            f"{self.group_addr_str()} />"
        )

    def __eq__(self, other: object) -> bool:
        """Equal operator."""
        for key, value in self.__dict__.items():
            if key == "after_update_cb":
                continue
            if key not in other.__dict__:
                return False
            if other.__dict__[key] != value:
                return False
        for key in other.__dict__:
            if key == "after_update_cb":
                continue
            if key not in self.__dict__:
                return False
        return True
