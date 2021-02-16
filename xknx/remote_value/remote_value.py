"""
Module for managing a remote value on the KNX bus.

Remote value can be :
- a group address for writing a KNX value,
- a group address for reading a KNX value,
- or a group of both representing the same value.
"""
from abc import ABC, abstractmethod
import logging
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Generic,
    Iterator,
    List,
    Optional,
    Union,
)

from xknx.dpt.dpt import DPTArray, DPTBinary, DPTPayloadType
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueResponse, GroupValueWrite

if TYPE_CHECKING:
    from xknx.telegram.address import GroupAddressableType
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")

AsyncCallbackType = Callable[[], Awaitable[None]]


class RemoteValue(ABC, Generic[DPTPayloadType]):
    """Class for managing remote knx value."""

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        xknx: "XKNX",
        group_address: Optional["GroupAddressableType"] = None,
        group_address_state: Optional["GroupAddressableType"] = None,
        sync_state: bool = True,
        device_name: Optional[str] = None,
        feature_name: Optional[str] = None,
        after_update_cb: Optional[AsyncCallbackType] = None,
        passive_group_addresses: Optional[List["GroupAddressableType"]] = None,
    ):
        """Initialize RemoteValue class."""
        # pylint: disable=too-many-arguments
        self.xknx: "XKNX" = xknx

        if group_address is not None:
            group_address = GroupAddress(group_address)
        if group_address_state is not None:
            group_address_state = GroupAddress(group_address_state)
        self.group_address: Optional[GroupAddress] = group_address
        self.group_address_state: Optional[GroupAddress] = group_address_state

        self.passive_group_addresses: List[
            GroupAddress
        ] = RemoteValue.get_passive_group_addresses(passive_group_addresses)

        self.device_name: str = "Unknown" if device_name is None else device_name
        self.feature_name: str = "Unknown" if feature_name is None else feature_name
        self.after_update_cb: Optional[AsyncCallbackType] = after_update_cb
        self.payload: Optional[DPTPayloadType] = None

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

    def has_group_address(self, group_address: GroupAddress) -> bool:
        """Test if device has given group address."""

        def _internal_addresses() -> Iterator[Optional[GroupAddress]]:
            """Yield all group_addresses."""
            yield self.group_address
            yield self.group_address_state
            yield from self.passive_group_addresses

        return group_address in _internal_addresses()

    @abstractmethod
    # TODO: typing - remove Optional
    def payload_valid(
        self, payload: Optional[Union[DPTArray, DPTBinary]]
    ) -> Optional[DPTPayloadType]:
        """Return payload if telegram payload may be parsed - to be implemented in derived class."""

    @abstractmethod
    def from_knx(self, payload: DPTPayloadType) -> Any:
        """Convert current payload to value - to be implemented in derived class."""

    @abstractmethod
    def to_knx(self, value: Any) -> DPTPayloadType:
        """Convert value to payload - to be implemented in derived class."""

    async def process(self, telegram: Telegram, always_callback: bool = False) -> bool:
        """Process incoming or outgoing telegram."""
        if not isinstance(
            telegram.destination_address, GroupAddress
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
        self.xknx.state_updater.update_received(self)
        if self.payload is None or always_callback or self.payload != _new_payload:
            self.payload = _new_payload
            if self.after_update_cb is not None:
                await self.after_update_cb()
        return True

    @property
    def value(self) -> Any:
        """Return current value."""
        if self.payload is None:
            return None
        return self.from_knx(self.payload)

    async def _send(self, payload: DPTPayloadType, response: bool = False) -> None:
        """Send payload as telegram to KNX bus."""
        if self.group_address is not None:
            telegram = Telegram(
                destination_address=self.group_address,
                payload=(
                    GroupValueResponse(payload)
                    if response
                    else GroupValueWrite(payload)
                ),
            )
            await self.xknx.telegrams.put(telegram)

    async def set(self, value: Any, response: bool = False) -> None:
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

        payload = self.to_knx(value)  # pylint: disable=assignment-from-no-return
        await self._send(payload, response)
        # self.payload is set and after_update_cb() called when the outgoing telegram is processed.

    async def respond(self) -> None:
        """Send current payload as GroupValueResponse telegram to KNX bus."""
        if self.payload is not None:
            await self._send(self.payload, response=True)

    async def read_state(self, wait_for_result: bool = False) -> None:
        """Send GroupValueRead telegram for state address to KNX bus."""
        if self.group_address_state is not None:
            # pylint: disable=import-outside-toplevel
            # TODO: send a ReadRequset and start a timeout from here instead of ValueReader
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
    def unit_of_measurement(self) -> Optional[str]:
        """Return the unit of measurement."""
        return None

    def group_addr_str(self) -> str:
        """Return object as readable string."""
        return "{}/{}/{}/{}".format(
            self.group_address.__repr__(),
            self.group_address_state.__repr__(),
            self.payload,
            self.value,
        )

    def __str__(self) -> str:
        """Return object as string representation."""
        return '<{} device_name="{}" feature_name="{}" {}/>'.format(
            self.__class__.__name__,
            self.device_name,
            self.feature_name,
            self.group_addr_str(),
        )

    def __eq__(self, other: Any) -> bool:
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

    @staticmethod
    def get_passive_group_addresses(
        passive_group_addresses: Optional[List["GroupAddressableType"]],
    ) -> List[GroupAddress]:
        """Obtain passive state group addresses."""
        if passive_group_addresses is None:
            return []
        return [GroupAddress(ga) for ga in passive_group_addresses]
