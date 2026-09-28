"""
Device is the base class for all implemented devices (e.g. Lights/Switches/Sensors).

It provides basis functionality for reading the state from the KNX bus.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextvars import ContextVar
from dataclasses import dataclass
import logging
from typing import TYPE_CHECKING, Any, Self, cast

from xknx.remote_value import RemoteValue
from xknx.telegram import (
    GroupReadTelegram,
    GroupValueTelegram,
    Telegram,
    current_telegram_context,
)
from xknx.telegram.address import DeviceGroupAddress
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite
from xknx.typing import DeviceCallbackType

if TYPE_CHECKING:
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")

# Telegram currently processed by a device. Being a ContextVar, tasks started by
# devices while processing (debouncers, travel updates, counters) inherit it as their
# cause. It is cleared while device updated callbacks run, so application code never
# inherits it.
_processing_telegram: ContextVar[Telegram | None] = ContextVar(
    "xknx_processing_telegram", default=None
)


@dataclass(frozen=True, slots=True)
class DeviceUpdate:
    """
    Cause of a device update passed to device updated callbacks.

    Attributes:
        telegram: The telegram that caused the update - incoming or outgoing. For
            updates run from a task started by the device, this is the telegram that
            started the task, eg. the one starting a covers travel. None if no telegram
            caused it, eg. `RemoteValue.update_value()` or a movement started by
            `Cover.set_position()` before its telegram was processed. Work scheduled
            from a device updated callback doesn't inherit the cause - pass
            `update.context` to `telegram_context()` to attribute it explicitly.
        context: The application defined context of the update. `telegram.context`
            if a telegram caused it, else the one of the active `telegram_context()`.

    """

    telegram: Telegram | None = None
    context: Any = None

    @classmethod
    def current(cls) -> DeviceUpdate:
        """Return the cause of an update happening now."""
        if (telegram := _processing_telegram.get()) is not None:
            return cls(telegram=telegram, context=telegram.context)
        return cls(context=current_telegram_context())


class Device(ABC):
    """Base class for devices."""

    def __init__(
        self,
        xknx: XKNX,
        *,
        name: str | None = None,
        device_updated_cb: DeviceCallbackType[Self] | None = None,
    ) -> None:
        """Initialize Device class."""
        self.xknx = xknx
        # assigned directly - the `name` setter needs the RemoteValues of the
        # subclass, which are only created after this constructor has returned
        self._name = name
        self.device_updated_cbs: list[DeviceCallbackType[Self]] = []
        if device_updated_cb is not None:
            self.register_device_updated_cb(device_updated_cb)

    @property
    def name(self) -> str:
        """Return name of device. Defaults to the class name."""
        if self._name is None:
            return type(self).__name__
        return self._name

    @name.setter
    def name(self, name: str | None) -> None:
        """Set name of device and pass it down to its RemoteValues."""
        self._name = name
        self._update_device_name()

    def _update_device_name(self) -> None:
        """Pass the current device name down to all RemoteValues of this device."""
        name = self.name
        for remote_value in self._iter_remote_values():
            remote_value.device_name = name

    def register_state_updater(self) -> None:
        """Register device addresses for StateUpdater."""
        for remote_value in self._iter_remote_values():
            remote_value.register_state_updater()

    def unregister_state_updater(self) -> None:
        """Unregister device addresses from StateUpdater."""
        for remote_value in self._iter_remote_values():
            remote_value.unregister_state_updater()

    def async_start_tasks(self) -> None:
        """Start async background tasks of device."""
        return

    def async_remove_tasks(self) -> None:
        """Remove all tasks of device."""
        return

    @abstractmethod
    def _iter_remote_values(self) -> Iterator[RemoteValue[Any]]:
        """Iterate the devices RemoteValue classes."""
        # yield self.remote_value
        # yield from (<list all used RemoteValue instances>)
        yield from ()

    def group_addresses(self) -> set[DeviceGroupAddress]:
        """Return all group addresses of this Device."""
        return {ga for rv in self._iter_remote_values() for ga in rv.group_addresses()}

    def register_device_updated_cb(
        self, device_updated_cb: DeviceCallbackType[Self]
    ) -> None:
        """Register device updated callback."""
        self.device_updated_cbs.append(device_updated_cb)

    def unregister_device_updated_cb(
        self, device_updated_cb: DeviceCallbackType[Self]
    ) -> None:
        """Unregister device updated callback."""
        if device_updated_cb in self.device_updated_cbs:
            self.device_updated_cbs.remove(device_updated_cb)

    def after_update(
        self: Self,
        *args: Any,  # a single argument may be passed if used as a RemoteValue callback
    ) -> None:
        """Execute callbacks after internal state has been changed."""
        update = DeviceUpdate.current()
        # callbacks get the cause as argument - work they schedule shall not inherit it
        token = _processing_telegram.set(None)
        try:
            for device_callback in self.device_updated_cbs:
                try:
                    device_callback(self, update)
                except Exception:  # pylint: disable=broad-except
                    logger.exception(
                        "Unexpected error while processing device_updated_cb for %s",
                        self,
                    )
        finally:
            _processing_telegram.reset(token)

    async def sync(self, wait_for_result: bool = False) -> None:
        """Read states of device from KNX bus."""
        for remote_value in self._iter_remote_values():
            await remote_value.read_state(wait_for_result=wait_for_result)

    def process(self, telegram: Telegram) -> None:
        """Process incoming or outgoing telegram."""
        token = _processing_telegram.set(telegram)
        try:
            if isinstance(telegram.payload, GroupValueWrite):
                self.process_group_write(cast("Telegram[GroupValueWrite]", telegram))
            elif isinstance(telegram.payload, GroupValueResponse):
                self.process_group_response(
                    cast("Telegram[GroupValueResponse]", telegram)
                )
            elif isinstance(telegram.payload, GroupValueRead):
                self.process_group_read(cast("GroupReadTelegram", telegram))
        finally:
            _processing_telegram.reset(token)

    def process_group_read(self, telegram: GroupReadTelegram) -> None:
        """Process incoming GroupValueRead telegrams."""
        # The default is, that devices don't answer to group reads
        return

    def process_group_response(self, telegram: Telegram[GroupValueResponse]) -> None:
        """Process incoming GroupValueResponse telegrams."""
        # Per default mapped to group write.
        self.process_group_write(telegram)

    def process_group_write(self, telegram: GroupValueTelegram) -> None:
        """Process incoming GroupValueWrite telegrams."""
        # The default is, that devices don't process group writes
        return

    def get_name(self) -> str:
        """Return name of device."""
        return self.name

    def has_group_address(self, group_address: DeviceGroupAddress) -> bool:
        """Test if device has given group address."""
        return any(
            group_address in remote_value.group_addresses()
            for remote_value in self._iter_remote_values()
        )
