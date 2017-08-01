"""
Module for managing a cover via KNX.

It provides functionality for

* moving cover up/down or to a specific position
* reading the current state from KNX bus.
* Cover will also predict the current position.
"""
import asyncio
from xknx.knx import Address, DPTBinary, DPTArray
from xknx.exceptions import CouldNotParseTelegram
from .device import Device
from .travelcalculator import TravelCalculator

class Cover(Device):
    """Class for managing a cover."""

    # Average typical travel time of a cover
    DEFAULT_TRAVEL_TIME_DOWN = 22
    DEFAULT_TRAVEL_TIME_UP = 22

    def __init__(self,
                 xknx,
                 name,
                 group_address_long=None,
                 group_address_short=None,
                 group_address_position=None,
                 group_address_position_feedback=None,
                 travel_time_down=DEFAULT_TRAVEL_TIME_DOWN,
                 travel_time_up=DEFAULT_TRAVEL_TIME_UP,
                 device_updated_cb=None):
        """Initialize Cover class."""
        # pylint: disable=too-many-arguments
        Device.__init__(self, xknx, name, device_updated_cb)

        if isinstance(group_address_long, (str, int)):
            group_address_long = Address(group_address_long)
        if isinstance(group_address_short, (str, int)):
            group_address_short = Address(group_address_short)
        if isinstance(group_address_position, (str, int)):
            group_address_position = Address(group_address_position)
        if isinstance(group_address_position_feedback, (str, int)):
            group_address_position_feedback = \
                Address(group_address_position_feedback)

        self.group_address_long = group_address_long
        self.group_address_short = group_address_short
        self.group_address_position = group_address_position
        self.group_address_position_feedback = group_address_position_feedback
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
        group_address_position_feedback = \
            config.get('group_address_position_feedback')
        travel_time_down = \
            config.get('travel_time_down', cls.DEFAULT_TRAVEL_TIME_DOWN)
        travel_time_up = \
            config.get('travel_time_up', cls.DEFAULT_TRAVEL_TIME_UP)

        return cls(xknx,
                   name,
                   group_address_long=group_address_long,
                   group_address_short=group_address_short,
                   group_address_position=group_address_position,
                   group_address_position_feedback=\
                        group_address_position_feedback,
                   travel_time_down=travel_time_down,
                   travel_time_up=travel_time_up)


    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return (self.group_address_long == group_address) \
            or (self.group_address_short == group_address) \
            or (self.group_address_position_feedback == group_address)


    def supports_direct_positioning(self):
        """Return if cover is supporting direct positioning."""
        return self.group_address_position is not None


    def __str__(self):
        """Return object as readable string."""
        return '<Cover name="{0}" ' \
                'group_address_long="{1}" ' \
                'group_address_short="{2}" ' \
                'group_address_position="{3}" ' \
                'group_address_position_feedback="{4}" ' \
                'travel_time_down="{5}" ' \
                'travel_time_up="{6}" />' \
                .format(
                    self.name,
                    self.group_address_long,
                    self.group_address_short,
                    self.group_address_position,
                    self.group_address_position_feedback,
                    self.travel_time_down,
                    self.travel_time_up)

    @asyncio.coroutine
    def set_down(self):
        """Move cover down."""
        if self.group_address_long is None:
            self.xknx.logger.warning("group_address_long not defined for device %s", self.get_name())
            return
        yield from self.send(self.group_address_long, DPTBinary(1))
        self.travelcalculator.start_travel_down()

    @asyncio.coroutine
    def set_up(self):
        """Move cover up."""
        if self.group_address_long is None:
            self.xknx.logger.warning("group_address_long not defined for device %s", self.get_name())
            return
        yield from self.send(self.group_address_long, DPTBinary(0))
        self.travelcalculator.start_travel_up()

    @asyncio.coroutine
    def set_short_down(self):
        """Move cover short down."""
        if self.group_address_short is None:
            self.xknx.logger.warning("group_address_short not defined for device %s", self.get_name())
            return
        yield from self.send(self.group_address_short, DPTBinary(1))

    @asyncio.coroutine
    def set_short_up(self):
        """Move cover short up."""
        if self.group_address_short is None:
            self.xknx.logger.warning("group_address_short not defined for device %s", self.get_name())
            return
        yield from self.send(self.group_address_short, DPTBinary(0))

    @asyncio.coroutine
    def stop(self):
        """Stop cover."""
        # Thats the KNX way of doing this. electrical engineers ... m-)
        yield from self.set_short_down()
        self.travelcalculator.stop()

    @asyncio.coroutine
    def set_position(self, position):
        """Move dover to a desginated postion."""
        if not self.supports_direct_positioning():

            current_position = self.current_position()
            if position > current_position:
                yield from self.send(self.group_address_long, DPTBinary(1))
            elif position < current_position:
                yield from self.send(self.group_address_long, DPTBinary(0))
            self.travelcalculator.start_travel(position)
            return
        yield from self.send(self.group_address_position, DPTArray(position))
        self.travelcalculator.start_travel(position)

    @asyncio.coroutine
    def auto_stop_if_necessary(self):
        """Do auto stop if necessary."""
        # If device does not support auto_positioning,
        # we have to ttop the device when position is reached.
        # unless device was traveling to fully open
        # or fully closed state
        if (
                not self.supports_direct_positioning() and
                self.position_reached() and
                not self.is_open() and
                not self.is_closed()):
            yield from self.stop()

    @asyncio.coroutine
    def do(self, action):
        """Method for executing 'do' commands."""
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
        if self.group_address_position_feedback is None:
            self.xknx.logger.warning("group_position not defined for device %s", self.get_name())
            return[]
        if self.travelcalculator.is_traveling():
            # Cover is traveling, requesting state will return false results
            return[]

        return [self.group_address_position_feedback,]

    @asyncio.coroutine
    def process(self, telegram):
        """Process incoming telegram."""
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 1:
            raise CouldNotParseTelegram()
        self.travelcalculator.set_position(telegram.payload.value[0])
        yield from self.after_update()


    def current_position(self):
        """Return current position of cover."""
        return self.travelcalculator.current_position()


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


    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
