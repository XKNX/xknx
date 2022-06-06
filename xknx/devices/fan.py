"""
Module for managing a fan via KNX.

It provides functionality for

* setting fan to specific speed / step
* reading the current speed from KNX bus.
"""
from __future__ import annotations

from enum import Enum
import logging
from typing import TYPE_CHECKING, Any, Iterator

from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueDptValue1Ucount,
    RemoteValueScaling,
    RemoteValueSwitch,
)

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class FanSpeedMode(Enum):
    """Enum for setting the fan speed mode."""

    PERCENT = 1
    STEP = 2


class Fan(Device):
    """Class for managing a fan."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address_speed: GroupAddressesType | None = None,
        group_address_speed_state: GroupAddressesType | None = None,
        group_address_oscillation: GroupAddressesType | None = None,
        group_address_oscillation_state: GroupAddressesType | None = None,
        group_address_switch: GroupAddressesType | None = None,
        group_address_switch_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        device_updated_cb: DeviceCallbackType[Fan] | None = None,
        max_step: int | None = None,
    ):
        """Initialize fan class."""
        super().__init__(xknx, name, device_updated_cb)

        self.speed: RemoteValueDptValue1Ucount | RemoteValueScaling
        self.mode = FanSpeedMode.STEP if max_step else FanSpeedMode.PERCENT
        self.max_step = max_step

        # If there is no dedicated switch GA, then the speed GA of the fan
        # controls the on/off behavior as well.
        self.switch = RemoteValueSwitch(
            xknx,
            group_address_switch,
            group_address_switch_state,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Switch",
            after_update_cb=self.after_update,
        )

        if self.mode == FanSpeedMode.STEP:
            self.speed = RemoteValueDptValue1Ucount(
                xknx,
                group_address_speed,
                group_address_speed_state,
                sync_state=sync_state,
                device_name=self.name,
                feature_name="Speed",
                after_update_cb=self.after_update,
            )
        else:
            self.speed = RemoteValueScaling(
                xknx,
                group_address_speed,
                group_address_speed_state,
                sync_state=sync_state,
                device_name=self.name,
                feature_name="Speed",
                after_update_cb=self.after_update,
                range_from=0,
                range_to=100,
            )

        self.oscillation = RemoteValueSwitch(
            xknx,
            group_address_oscillation,
            group_address_oscillation_state,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Oscillation",
            after_update_cb=self.after_update,
        )

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any, Any]]:
        """Iterate the devices RemoteValue classes."""
        yield from (self.switch, self.speed, self.oscillation)

    @property
    def supports_oscillation(self) -> bool:
        """Return if fan supports oscillation."""
        return self.oscillation.initialized

    @property
    def has_on_off_switch(self) -> bool:
        """Return if fan has separate speed GA, which in turns means a separate on/off switch GA."""
        return self.switch.initialized

    @property
    def is_on(self) -> bool:
        """Return the current fan state of the device."""
        if self.switch.initialized:
            return bool(self.switch.value)
        return bool(self.current_speed)

    async def turn_on(self, speed: int) -> None:
        """Turn on fan."""
        if self.switch.initialized:
            await self.set_on()
        else:
            await self.set_speed(speed)

    async def turn_off(self) -> None:
        """Turn off fan."""
        if self.switch.initialized:
            await self.set_off()
        else:
            await self.set_speed(0)

    async def set_on(self) -> None:
        """Switch on fan."""
        await self.switch.on()

    async def set_off(self) -> None:
        """Switch off fan."""
        await self.switch.off()

    async def set_speed(self, speed: int) -> None:
        """Set the fan to a designated speed."""
        await self.speed.set(speed)

    async def set_oscillation(self, oscillation: bool) -> None:
        """Set the fan oscillation mode on or off."""
        await self.oscillation.set(oscillation)

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        await self.switch.process(telegram)
        await self.speed.process(telegram)
        await self.oscillation.process(telegram)

    @property
    def current_speed(self) -> int | None:
        """Return current speed of fan."""
        return self.speed.value

    @property
    def current_oscillation(self) -> bool | None:
        """Return true if the fan is oscillating."""
        return self.oscillation.value

    def __str__(self) -> str:
        """Return object as readable string."""

        str_oscillation = (
            ""
            if not self.supports_oscillation
            else f" oscillation={self.oscillation.group_addr_str()}"
        )

        return f'<Fan name="{self.name}" speed={self.speed.group_addr_str()}{str_oscillation} />'
