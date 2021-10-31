"""
Module for managing a remote value on the KNX bus.

Remote value can be :
- a group address for writing a KNX value,
- a group address for reading a KNX value,
- or a group of both representing the same value.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import (
    TYPE_CHECKING,
    Awaitable,
    Callable,
    Generic,
    Iterator,
    List,
    TypeVar,
    Union,
)

from xknx.dpt.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
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

AsyncCallbackType = Callable[[], Awaitable[None]]
DPTPayloadType = TypeVar(
    "DPTPayloadType", DPTArray, DPTBinary, Union[DPTArray, DPTBinary]
)
GroupAddressesType = Union["DeviceAddressableType", List["DeviceAddressableType"]]
ValueType = TypeVar("ValueType")


class RemoteValue(ABC, Generic[DPTPayloadType, ValueType]):
    """Class for managing remote knx value."""

    def __init__(
        self,
        xknx: XKNX,
        group_address: GroupAddressesType | None = None,
        group_address_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        device_name: str | None = None,
        feature_name: str | None = None,
        after_update_cb: AsyncCallbackType | None = None,
    ):
        """Initialize RemoteValue class."""
        self.xknx: XKNX = xknx
        self.passive_group_addresses: list[DeviceGroupAddress] = []

        def unpack_group_addresses(
            addresses: GroupAddressesType | None,
        ) -> DeviceGroupAddress | None:
            """Parse group addresses and assign passive addresses when given."""
            if addresses is None:
                return None
            if not isinstance(addresses, list):
                return parse_device_group_address(addresses)
            active, *passive = map(parse_device_group_address, addresses)
            self.passive_group_addresses.extend(passive)  # type: ignore
            return active

        self.group_address = unpack_group_addresses(group_address)
        self.group_address_state = unpack_group_addresses(group_address_state)

        self.device_name: str = "Unknown" if device_name is None else device_name
        self.feature_name: str = "Unknown" if feature_name is None else feature_name
        self._value: ValueType | None = None
        self.telegram: Telegram | None = None
        self.after_update_cb: AsyncCallbackType | None = after_update_cb

        if sync_state and self.group_address_state:
            self.xknx.state_updater.register_remote_value(
                self, tracker_options=sync_state
            )

    def __del__(self) -> None:
        """Destructor. Removing self from StateUpdater if was registered."""
        try:
            self.xknx.state_updater.unregister_remote_value(self)
        except (KeyError, AttributeError):
            # KeyError if it was never added to StateUpdater
            # AttributeError if instantiation failed (tests mostly)
            pass

    @property
    def value(self) -> ValueType | None:
        """Get current value."""
        return self._value

    @value.setter
    def value(self, value: ValueType | None) -> None:
        """Set new value without creating a Telegram or calling after_update_cb. Raises ConversionError on invalid value."""
        if value is not None:
            # raises ConversionError on invalid value
            self.to_knx(value)
        self._value = value

    async def update_value(self, value: ValueType | None) -> None:
        """Set new value without creating a Telegram. Awaits after_update_cb. Raises ConversionError on invalid value."""
        self.value = value
        if self.after_update_cb is not None:
            await self.after_update_cb()

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

    def has_group_address(self, group_address: DeviceGroupAddress) -> bool:
        """Test if device has given group address."""

        def remote_value_addresses() -> Iterator[DeviceGroupAddress | None]:
            """Yield all group_addresses."""
            yield self.group_address
            yield self.group_address_state
            yield from self.passive_group_addresses

        return group_address in remote_value_addresses()

    @abstractmethod
    # TODO: typing - remove Optional
    def payload_valid(
        self, payload: DPTArray | DPTBinary | None
    ) -> DPTPayloadType | None:
        """Return payload if telegram payload may be parsed - to be implemented in derived class."""

    @abstractmethod
    def from_knx(self, payload: DPTPayloadType) -> ValueType:
        """Convert current payload to value - to be implemented in derived class."""

    @abstractmethod
    def to_knx(self, value: ValueType) -> DPTPayloadType:
        """Convert value to payload - to be implemented in derived class."""

    async def process(self, telegram: Telegram, always_callback: bool = False) -> bool:
        """Process incoming or outgoing telegram."""
        if not isinstance(
            telegram.destination_address, (GroupAddress, InternalGroupAddress)
        ) or not self.has_group_address(telegram.destination_address):
            return False
        if not isinstance(
            telegram.payload,
            (
                GroupValueWrite,
                GroupValueResponse,
            ),
        ):
            raise CouldNotParseTelegram(
                "payload not a GroupValueWrite or GroupValueResponse",
                payload=str(telegram.payload),
                destination_address=str(telegram.destination_address),
                source_address=str(telegram.source_address),
                device_name=self.device_name,
                feature_name=self.feature_name,
            )
        _new_payload = self.payload_valid(telegram.payload.value)
        if _new_payload is None:
            raise CouldNotParseTelegram(
                "payload invalid",
                payload=str(telegram.payload),
                destination_address=str(telegram.destination_address),
                source_address=str(telegram.source_address),
                device_name=self.device_name,
                feature_name=self.feature_name,
            )
        decoded_payload = self.from_knx(_new_payload)
        self.xknx.state_updater.update_received(self)
        if self._value is None or always_callback or self._value != decoded_payload:
            self._value = decoded_payload
            self.telegram = telegram
            if self.after_update_cb is not None:
                await self.after_update_cb()
        return True

    async def _send(
        self, payload: DPTArray | DPTBinary, response: bool = False
    ) -> None:
        """Send payload as telegram to KNX bus."""
        if self.group_address is not None:
            telegram = Telegram(
                destination_address=self.group_address,
                payload=(
                    GroupValueResponse(payload)
                    if response
                    else GroupValueWrite(payload)
                ),
                source_address=self.xknx.current_address,
            )
            await self.xknx.telegrams.put(telegram)

    async def set(self, value: ValueType, response: bool = False) -> None:
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
        await self._send(payload, response)
        # self._value is set and after_update_cb() called when the outgoing telegram is processed.

    async def respond(self) -> None:
        """Send current payload as GroupValueResponse telegram to KNX bus."""
        if self._value is not None:
            payload = self.to_knx(self._value)
            await self._send(payload, response=True)

    async def read_state(self, wait_for_result: bool = False) -> None:
        """Send GroupValueRead telegram for state address to KNX bus."""
        if self.group_address_state is not None:
            # pylint: disable=import-outside-toplevel
            # TODO: send a ReadRequest and start a timeout from here instead of ValueReader
            #       cancel timeout form process(); delete ValueReader
            from xknx.core import ValueReader

            value_reader = ValueReader(self.xknx, self.group_address_state)
            if wait_for_result:
                telegram = await value_reader.read()
                if telegram is not None:
                    await self.process(telegram)
                else:
                    logger.warning(
                        "Could not sync group address '%s' (%s - %s)",
                        self.group_address_state,
                        self.device_name,
                        self.feature_name,
                    )
            else:
                await value_reader.send_group_read()

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
            f"{self.value.__repr__()} />"
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
        for key, value in other.__dict__.items():
            if key == "after_update_cb":
                continue
            if key not in self.__dict__:
                return False
        return True
