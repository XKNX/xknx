"""
Module for managing a cover via KNX.

It provides functionality for

* moving cover up/down or to a specific position
* reading the current state from KNX bus.
* Cover will also predict the current position.
"""
import asyncio

from .device import Device
from .group import (GroupScaling5001, GroupStep1007,
                    GroupUpDown1008)
from .travelcalculator import TravelCalculator


class Cover(Device):
    """Class for managing a cover."""

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-public-methods

    # Average typical travel time of a cover
    DEFAULT_TRAVEL_TIME_DOWN = 22
    DEFAULT_TRAVEL_TIME_UP = 22

    def __init__(self,
                 xknx,
                 name,
                 group_address_long=None,
                 group_address_short=None,
                 group_address_position=None,
                 group_address_position_state=None,
                 group_address_angle=None,
                 group_address_angle_state=None,
                 travel_time_down=DEFAULT_TRAVEL_TIME_DOWN,
                 travel_time_up=DEFAULT_TRAVEL_TIME_UP,
                 invert_position=False,
                 invert_angle=False,
                 device_updated_cb=None):
        """Initialize Cover class."""
        # pylint: disable=too-many-arguments
        Device.__init__(self, xknx, name, device_updated_cb)

        self.updown = GroupUpDown1008(
            xknx,
            group_address_long,
            after_update_cb=self.after_update,
            invert=invert_position)

        self.step = GroupStep1007(
            xknx,
            group_address_short,
            after_update_cb=self.after_update,
            invert=invert_position)

        self.position = GroupScaling5001(
            xknx,
            group_address_position,
            group_address_position_state,
            after_update_cb=self.after_update,
            invert=invert_position)

        self.angle = GroupScaling5001(
            xknx,
            group_address_angle,
            group_address_angle_state,
            after_update_cb=self.after_update,
            invert=invert_angle)

        self.travel_time_down = travel_time_down
        self.travel_time_up = travel_time_up

        self.travelcalculator = TravelCalculator(
            travel_time_down,
            travel_time_up)

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address_long = \
            config.get('group_address_long')
        group_address_short = \
            config.get('group_address_short')
        group_address_position = \
            config.get('group_address_position')
        group_address_position_state = \
            config.get('group_address_position_state')
        group_address_angle = \
            config.get('group_address_angle')
        group_address_angle_state = \
            config.get('group_address_angle_state')
        travel_time_down = \
            config.get('travel_time_down', cls.DEFAULT_TRAVEL_TIME_DOWN)
        travel_time_up = \
            config.get('travel_time_up', cls.DEFAULT_TRAVEL_TIME_UP)

        return cls(
            xknx,
            name,
            group_address_long=group_address_long,
            group_address_short=group_address_short,
            group_address_position=group_address_position,
            group_address_position_state=group_address_position_state,
            group_address_angle=group_address_angle,
            group_address_angle_state=group_address_angle_state,
            travel_time_down=travel_time_down,
            travel_time_up=travel_time_up)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return self.updown.has_group_address(group_address) \
            or self.step.has_group_address(group_address) \
            or self.position.has_group_address(group_address) \
            or self.angle.has_group_address(group_address)

    def __str__(self):
        """Return object as readable string."""
        return '<Cover name="{0}" ' \
            'updown"{1}" ' \
            'step="{2}" ' \
            'position="{3}" ' \
            'angle="{4}" '\
            'travel_time_down="{5}" ' \
            'travel_time_up="{6}" />' \
            .format(
                self.name,
                self.updown.group_addr_str(),
                self.step.group_addr_str(),
                self.position.group_addr_str(),
                self.angle.group_addr_str(),
                self.travel_time_down,
                self.travel_time_up)

    @asyncio.coroutine
    def set_down(self):
        """Move cover down."""
        yield from self.updown.down()
        self.travelcalculator.start_travel_down()

    @asyncio.coroutine
    def set_up(self):
        """Move cover up."""
        yield from self.updown.up()
        self.travelcalculator.start_travel_up()

    @asyncio.coroutine
    def set_short_down(self):
        """Move cover short down."""
        yield from self.step.increase()

    @asyncio.coroutine
    def set_short_up(self):
        """Move cover short up."""
        yield from self.step.decrease()

    @asyncio.coroutine
    def stop(self):
        """Stop cover."""
        # Thats the KNX way of doing this. electrical engineers ... m-)
        yield from self.step.increase()
        self.travelcalculator.stop()

    @asyncio.coroutine
    def set_position(self, position):
        """Move cover to a desginated postion."""
        # No direct positioning group address defined
        if not self.position.group_address:
            current_position = self.current_position()
            if position < current_position:
                yield from self.updown.down()
            elif position > current_position:
                yield from self.updown.up()
            self.travelcalculator.start_travel(position)
            return

        yield from self.position.set(position)
        self.travelcalculator.start_travel(position)

    @asyncio.coroutine
    def set_angle(self, angle):
        """Move cover to designated angle."""
        if not self.supports_angle:
            return
        yield from self.angle.set(angle)
        yield from self.after_update()

    @asyncio.coroutine
    def auto_stop_if_necessary(self):
        """Do auto stop if necessary."""
        # If device does not support auto_positioning,
        # we have to ttop the device when position is reached.
        # unless device was traveling to fully open
        # or fully closed state
        if (
                not self.position.group_address and
                self.position_reached() and
                not self.is_open() and
                not self.is_closed()):
            yield from self.stop()

    @asyncio.coroutine
    def do(self, action):
        """Execute 'do' commands."""
        if action == "up":
            yield from self.set_up()
        elif action == "short_up":
            yield from self.set_short_up()
        elif action == "down":
            yield from self.set_down()
        elif action == "short_down":
            yield from self.set_short_down()
        else:
            self.xknx.logger.warning("Could not understand action %s for device %s", action, self.get_name())

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        if self.travelcalculator.is_traveling():
            # Cover is traveling, requesting state will return false results
            return[]
        state_addresses = []
        state_addresses.extend(self.position.state_addresses())
        state_addresses.extend(self.angle.state_addresses())
        return state_addresses

    @asyncio.coroutine
    def process(self, telegram):
        """Process incoming telegram."""
        position_processed = yield from self.position.process(telegram)
        if position_processed:
            self.travelcalculator.set_position(self.position.value)
            yield from self.after_update()

        yield from self.angle.process(telegram)

    def current_position(self):
        """Return current position of cover."""
        return self.travelcalculator.current_position()

    def current_angle(self):
        """Return current tilt angle of cover."""
        return self.angle.value

    def is_traveling(self):
        """Return if cover is traveling at the moment."""
        return self.travelcalculator.is_traveling()

    def position_reached(self):
        """Return if cover has reached its final position."""
        return self.travelcalculator.position_reached()

    def is_open(self):
        """Return if cover is open."""
        return self.travelcalculator.is_open()

    def is_closed(self):
        """Return if cover is closed."""
        return self.travelcalculator.is_closed()

    @property
    def supports_position(self):
        """Return if cover supports direct positioning."""
        return self.position.initialized

    @property
    def supports_angle(self):
        """Return if cover supports tilt angle."""
        return self.angle.initialized

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
