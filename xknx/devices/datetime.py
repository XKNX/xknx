"""Module for broadcasting date/time to the KNX bus, optionally broadcasting localtime periodically."""

from __future__ import annotations

from abc import abstractmethod
import asyncio
from collections.abc import Iterator
import datetime
from functools import partial
import logging
import time
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from xknx.core import Task
from xknx.dpt.dpt_10 import KNXDay, KNXTime
from xknx.dpt.dpt_11 import KNXDate
from xknx.dpt.dpt_19 import KNXDateTime, KNXDayOfWeek
from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueDate,
    RemoteValueDateTime,
    RemoteValueTime,
)
from xknx.typing import Self

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


BROADCAST_MINUTES = 60

_RemoteValueTimeT = TypeVar(
    "_RemoteValueTimeT", RemoteValueTime, RemoteValueDate, RemoteValueDateTime
)


class _DateTimeBase(Device, Generic[_RemoteValueTimeT]):
    """Base class for virtual date/time device."""

    _remote_value_cls: type[_RemoteValueTimeT]  # set in subclass

    remote_value: _RemoteValueTimeT

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        localtime: bool | datetime.tzinfo = True,
        group_address: GroupAddressesType = None,
        group_address_state: GroupAddressesType = None,
        respond_to_read: bool = False,
        sync_state: bool | int | float | str = True,
        device_updated_cb: DeviceCallbackType[Self] | None = None,
    ) -> None:
        """Initialize DateTime class."""
        super().__init__(xknx, name, device_updated_cb)
        self.localtime = bool(localtime)
        self._localtime_zone = (
            localtime if isinstance(localtime, datetime.tzinfo) else None
        )
        if localtime and bool(group_address_state):
            logger.warning(
                "State address invalid in %s device when using `localtime=True`. Ignoring `group_address_state=%s` argument.",
                self.__class__.__name__,
                group_address_state,
            )
            # state address invalid for localtime - therefore sync_state doesn't apply for localtime
            group_address_state = None
        self.respond_to_read = respond_to_read
        self.remote_value = self._remote_value_cls(
            xknx,
            group_address=group_address,
            group_address_state=group_address_state,
            sync_state=sync_state,
            device_name=name,
            after_update_cb=self.after_update,
        )
        self._broadcast_task: Task | None = None

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any]]:
        """Iterate the devices RemoteValue classes."""
        yield self.remote_value

    @property
    @abstractmethod
    def value(self) -> datetime.datetime | datetime.date | datetime.time | None:
        """Return the current date/time value."""

    def async_start_tasks(self) -> None:
        """Create an asyncio.Task for broadcasting local time periodically if `localtime` is set."""
        if not self.localtime:
            return None

        async def broadcast_loop(self: Self, minutes: int) -> None:
            """Endless loop for broadcasting local time."""
            while True:
                self.broadcast_localtime()
                await asyncio.sleep(minutes * 60)

        self._broadcast_task = self.xknx.task_registry.register(
            name=f"datetime.broadcast_{id(self)}",
            async_func=partial(broadcast_loop, self, BROADCAST_MINUTES),
            restart_after_reconnect=True,
        ).start()

    def async_remove_tasks(self) -> None:
        """Stop background tasks of device."""
        if self._broadcast_task is not None:
            self.xknx.task_registry.unregister(self._broadcast_task.name)
            self._broadcast_task = None

    @abstractmethod
    def broadcast_localtime(self, response: bool = False) -> None:
        """Broadcast the local time to KNX bus."""
        # self.remote_value.set(now, response=response)

    @abstractmethod
    async def set(self, value: Any) -> None:
        """Set time and send to KNX bus."""
        # self.remote_value.set(value)

    def process_group_write(self, telegram: Telegram) -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        self.remote_value.process(telegram)

    def process_group_read(self, telegram: Telegram) -> None:
        """Process incoming GROUP READ telegram."""
        if self.localtime:
            self.broadcast_localtime(True)
        elif (
            self.respond_to_read
            and telegram.destination_address == self.remote_value.group_address
        ):
            self.remote_value.respond()

    async def sync(self, wait_for_result: bool = False) -> None:
        """Read state of device from KNX bus. Used here to broadcast time to KNX bus."""
        if self.localtime:
            self.broadcast_localtime(response=False)
        else:
            await super().sync(wait_for_result)

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<{self.__class__.__name__} name="{self.name}" '
            f"remote_value={self.remote_value.group_addr_str()} />"
        )


class TimeDevice(_DateTimeBase[RemoteValueTime]):
    """Class for virtual time device."""

    _remote_value_cls = RemoteValueTime

    @property
    def value(self) -> datetime.time | None:
        """Return the current time value."""
        return self.remote_value.value.as_time() if self.remote_value.value else None

    async def set(self, value: KNXTime | datetime.time) -> None:
        """Set time and send to KNX bus."""
        if isinstance(value, datetime.time):
            value = KNXTime.from_time(value)
        self.remote_value.set(value)

    def broadcast_localtime(self, response: bool = False) -> None:
        """Broadcast the local time to KNX bus."""
        now = datetime.datetime.now(self._localtime_zone)
        knx_time = KNXTime.from_time(now.time())
        knx_time.day = KNXDay(now.weekday() + 1)
        self.remote_value.set(knx_time, response=response)


class DateDevice(_DateTimeBase[RemoteValueDate]):
    """Class for virtual date device."""

    _remote_value_cls = RemoteValueDate

    @property
    def value(self) -> datetime.date | None:
        """Return the current time value."""
        return self.remote_value.value.as_date() if self.remote_value.value else None

    async def set(self, value: KNXDate | datetime.date) -> None:
        """Set date and send to KNX bus."""
        if isinstance(value, datetime.date):
            value = KNXDate.from_date(value)
        self.remote_value.set(value)

    def broadcast_localtime(self, response: bool = False) -> None:
        """Broadcast the local date to KNX bus."""
        now = datetime.datetime.now(self._localtime_zone)
        self.remote_value.set(KNXDate.from_date(now.date()), response=response)


class DateTimeDevice(_DateTimeBase[RemoteValueDateTime]):
    """Class for virtual date/time device."""

    _remote_value_cls = RemoteValueDateTime

    timezone: datetime.tzinfo | None = None

    @property
    def value(self) -> datetime.datetime | None:
        """Return the current time value."""
        return (
            self.remote_value.value.as_datetime() if self.remote_value.value else None
        )

    async def set(self, value: KNXDateTime | datetime.datetime) -> None:
        """Set date/time and send to KNX bus."""
        if isinstance(value, datetime.datetime):
            value = KNXDateTime.from_datetime(value)
        self.remote_value.set(value)

    def broadcast_localtime(self, response: bool = False) -> None:
        """Broadcast the local date/time to KNX bus."""
        now = datetime.datetime.now(self._localtime_zone)
        knx_datetime = KNXDateTime.from_datetime(now)
        knx_datetime.day_of_week = KNXDayOfWeek(now.weekday() + 1)
        if self._localtime_zone is not None:
            dst = self._localtime_zone.dst(now)
            knx_datetime.dst = dst > datetime.timedelta(0) if dst is not None else False
        else:
            time_now = time.localtime()
            knx_datetime.dst = time_now.tm_isdst > 0
        knx_datetime.external_sync = True
        knx_datetime.source_reliable = True
        self.remote_value.set(knx_datetime, response=response)
