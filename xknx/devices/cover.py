"""
Module for managing a cover via KNX.

It provides functionality for

* moving cover up/down or to a specific position
* reading the current state from KNX bus.
* Cover will also predict the current position.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Iterator

from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueScaling,
    RemoteValueStep,
    RemoteValueSwitch,
    RemoteValueUpDown,
)

from .device import Device, DeviceCallbackType
from .travelcalculator import TravelCalculator, TravelStatus

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Cover(Device):
    """Class for managing a cover."""

    DEFAULT_TRAVEL_TIME_DOWN = 22
    DEFAULT_TRAVEL_TIME_UP = 22

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address_long: GroupAddressesType | None = None,
        group_address_short: GroupAddressesType | None = None,
        group_address_stop: GroupAddressesType | None = None,
        group_address_position: GroupAddressesType | None = None,
        group_address_position_state: GroupAddressesType | None = None,
        group_address_angle: GroupAddressesType | None = None,
        group_address_angle_state: GroupAddressesType | None = None,
        group_address_locked_state: GroupAddressesType | None = None,
        sync_state: bool | int | float | str = True,
        travel_time_down: float = DEFAULT_TRAVEL_TIME_DOWN,
        travel_time_up: float = DEFAULT_TRAVEL_TIME_UP,
        invert_position: bool = False,
        invert_angle: bool = False,
        device_updated_cb: DeviceCallbackType | None = None,
    ):
        """Initialize Cover class."""
        super().__init__(xknx, name, device_updated_cb)
        # self.after_update for position changes is called after updating the
        # travelcalculator (in process_group_write and set_*) - angle changes
        # are updated from RemoteValue objects
        self.updown = RemoteValueUpDown(
            xknx,
            group_address_long,
            device_name=self.name,
            after_update_cb=None,
            invert=invert_position,
        )

        self.step = RemoteValueStep(
            xknx,
            group_address_short,
            device_name=self.name,
            after_update_cb=self.after_update,
            invert=invert_position,
        )

        self.stop_ = RemoteValueSwitch(
            xknx,
            group_address=group_address_stop,
            sync_state=False,
            device_name=self.name,
            after_update_cb=None,
        )

        position_range_from = 100 if invert_position else 0
        position_range_to = 0 if invert_position else 100
        self.position_current = RemoteValueScaling(
            xknx,
            group_address_state=group_address_position_state,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Position",
            after_update_cb=self._current_position_from_rv,
            range_from=position_range_from,
            range_to=position_range_to,
        )
        self.position_target = RemoteValueScaling(
            xknx,
            group_address=group_address_position,
            device_name=self.name,
            feature_name="Target position",
            after_update_cb=self._target_position_from_rv,
            range_from=position_range_from,
            range_to=position_range_to,
        )

        angle_range_from = 100 if invert_angle else 0
        angle_range_to = 0 if invert_angle else 100
        self.angle = RemoteValueScaling(
            xknx,
            group_address_angle,
            group_address_angle_state,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Tilt angle",
            after_update_cb=self.after_update,
            range_from=angle_range_from,
            range_to=angle_range_to,
        )

        self.locked = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_locked_state,
            sync_state=sync_state,
            device_name=self.name,
            feature_name="Locked",
            after_update_cb=self.after_update,
        )

        self.travel_time_down = travel_time_down
        self.travel_time_up = travel_time_up

        self.travelcalculator = TravelCalculator(travel_time_down, travel_time_up)
        self.travel_direction_tilt: TravelStatus | None = None

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any, Any]]:
        """Iterate the devices RemoteValue classes."""
        yield self.updown
        yield self.step
        yield self.stop_
        yield self.position_current
        yield self.position_target
        yield self.angle
        yield self.locked

    async def set_down(self) -> None:
        """Move cover down."""
        if self.updown.writable:
            await self.updown.down()
            self.travelcalculator.start_travel_down()
            self.travel_direction_tilt = None
            await self.after_update()
        elif self.position_target.writable:
            await self.position_target.set(self.travelcalculator.position_closed)

    async def set_up(self) -> None:
        """Move cover up."""
        if self.updown.writable:
            await self.updown.up()
            self.travelcalculator.start_travel_up()
            self.travel_direction_tilt = None
            await self.after_update()
        elif self.position_target.writable:
            await self.position_target.set(self.travelcalculator.position_open)

    async def set_short_down(self) -> None:
        """Move cover short down."""
        await self.step.increase()

    async def set_short_up(self) -> None:
        """Move cover short up."""
        await self.step.decrease()

    async def stop(self) -> None:
        """Stop cover."""
        if self.stop_.writable:
            await self.stop_.on()
        elif self.step.writable:
            if TravelStatus.DIRECTION_UP in (
                self.travelcalculator.travel_direction,
                self.travel_direction_tilt,
            ):
                await self.step.decrease()
            elif TravelStatus.DIRECTION_DOWN in (
                self.travelcalculator.travel_direction,
                self.travel_direction_tilt,
            ):
                await self.step.increase()
        else:
            logger.warning("Stop not supported for device %s", self.get_name())
            return
        self.travelcalculator.stop()
        self.travel_direction_tilt = None
        await self.after_update()

    async def set_position(self, position: int) -> None:
        """Move cover to a desginated postion."""
        if not self.position_target.writable:
            # No direct positioning group address defined
            # fully open or close is always possible even if current position is not known
            current_position = self.current_position()
            if current_position is None:
                if position == self.travelcalculator.position_open:
                    await self.updown.up()
                elif position == self.travelcalculator.position_closed:
                    await self.updown.down()
                else:
                    logger.warning(
                        "Current position unknown. Initialize cover by moving to end position."
                    )
                    return
            elif position < current_position:
                await self.updown.up()
            elif position > current_position:
                await self.updown.down()
            self.travelcalculator.start_travel(position)
            await self.after_update()
        else:
            await self.position_target.set(position)

    async def _target_position_from_rv(self) -> None:
        """Update the target postion from RemoteValue (Callback)."""
        new_target = self.position_target.value
        if new_target is not None:
            self.travelcalculator.start_travel(new_target)
            await self.after_update()

    async def _current_position_from_rv(self) -> None:
        """Update the current postion from RemoteValue (Callback)."""
        position_before_update = self.travelcalculator.current_position()
        new_position = self.position_current.value
        if new_position is not None:
            if self.is_traveling():
                self.travelcalculator.update_position(new_position)
            else:
                self.travelcalculator.set_position(new_position)
            if position_before_update != self.travelcalculator.current_position():
                await self.after_update()

    async def set_angle(self, angle: int) -> None:
        """Move cover to designated angle."""
        if not self.supports_angle:
            logger.warning("Angle not supported for device %s", self.get_name())
            return

        current_angle = self.current_angle()
        self.travel_direction_tilt = (
            TravelStatus.DIRECTION_DOWN
            if current_angle is not None and angle >= current_angle
            else TravelStatus.DIRECTION_UP
        )

        await self.angle.set(angle)

    async def auto_stop_if_necessary(self) -> None:
        """Do auto stop if necessary."""
        # If device does not support auto_positioning,
        # we have to stop the device when position is reached,
        # unless device was traveling to fully open
        # or fully closed state.
        if (
            self.supports_stop
            and not self.position_target.writable
            and self.position_reached()
            and not self.is_open()
            and not self.is_closed()
        ):
            await self.stop()

    async def sync(self, wait_for_result: bool = False) -> None:
        """Read states of device from KNX bus."""
        await self.position_current.read_state(wait_for_result=wait_for_result)
        await self.angle.read_state(wait_for_result=wait_for_result)

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        # call after_update to account for travelcalculator changes
        if await self.updown.process(telegram):
            if (
                not self.is_opening()
                and self.updown.value == RemoteValueUpDown.Direction.UP
            ):
                self.travelcalculator.start_travel_up()
                await self.after_update()
            elif (
                not self.is_closing()
                and self.updown.value == RemoteValueUpDown.Direction.DOWN
            ):
                self.travelcalculator.start_travel_down()
                await self.after_update()
        # stop from bus
        if await self.stop_.process(telegram) or await self.step.process(telegram):
            if self.is_traveling():
                self.travelcalculator.stop()
                await self.after_update()

        await self.position_current.process(telegram, always_callback=True)
        await self.position_target.process(telegram)
        await self.angle.process(telegram)
        await self.locked.process(telegram)

    def current_position(self) -> int | None:
        """Return current position of cover."""
        return self.travelcalculator.current_position()

    def current_angle(self) -> int | None:
        """Return current tilt angle of cover."""
        return self.angle.value

    def is_locked(self) -> bool | None:
        """Return if the cover is currently locked for manual movement."""
        return self.locked.value

    def is_traveling(self) -> bool:
        """Return if cover is traveling at the moment."""
        return self.travelcalculator.is_traveling()

    def position_reached(self) -> bool:
        """Return if cover has reached its final position."""
        return self.travelcalculator.position_reached()

    def is_open(self) -> bool:
        """Return if cover is open."""
        return self.travelcalculator.is_open()

    def is_closed(self) -> bool:
        """Return if cover is closed."""
        return self.travelcalculator.is_closed()

    def is_opening(self) -> bool:
        """Return if the cover is opening or not."""
        return self.travelcalculator.is_opening()

    def is_closing(self) -> bool:
        """Return if the cover is closing or not."""
        return self.travelcalculator.is_closing()

    @property
    def supports_stop(self) -> bool:
        """Return if cover supports manual stopping."""
        return self.stop_.writable or self.step.writable

    @property
    def supports_locked(self) -> bool:
        """Return if cover supports locking."""
        return self.locked.initialized

    @property
    def supports_position(self) -> bool:
        """Return if cover supports direct positioning."""
        return self.position_target.initialized

    @property
    def supports_angle(self) -> bool:
        """Return if cover supports tilt angle."""
        return self.angle.initialized

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<Cover name="{self.name}" '
            f"updown={self.updown.group_addr_str()} "
            f"step={self.step.group_addr_str()} "
            f"stop_={self.stop_.group_addr_str()} "
            f"position_current={self.position_current.group_addr_str()} "
            f"position_target={self.position_target.group_addr_str()} "
            f"angle={self.angle.group_addr_str()} "
            f"locked={self.locked.group_addr_str()} "
            f'travel_time_down="{self.travel_time_down}" '
            f'travel_time_up="{self.travel_time_up}" '
            "/>"
        )
