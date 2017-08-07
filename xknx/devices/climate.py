"""
Module for managing the climate within a room.

* It reads/listens to a temperature address from KNX bus.
* Manages and sends the desired setpoint to KNX bus.
"""
import time
import datetime
import asyncio
from xknx.knx import Address, DPTArray, DPTTemperature
from xknx.exceptions import CouldNotParseTelegram
from .device import Device


class Climate(Device):
    """Class for managing the climate."""

    def __init__(self,
                 xknx,
                 name,
                 group_address_temperature=None,
                 group_address_setpoint=None,
                 device_updated_cb=None):
        """Initialize Climate class."""
        # pylint: disable=too-many-arguments
        Device.__init__(self, xknx, name, device_updated_cb)
        if isinstance(group_address_temperature, (str, int)):
            group_address_temperature = Address(group_address_temperature)
        if isinstance(group_address_setpoint, (str, int)):
            group_address_setpoint = Address(group_address_setpoint)

        self.group_address_temperature = group_address_temperature
        self.group_address_setpoint = group_address_setpoint
        self.last_set = None
        self.temperature = None
        self.setpoint = None

        self.supports_temperature = \
            group_address_temperature is not None
        self.supports_setpoint = \
            group_address_setpoint is not None

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address_temperature = \
            config.get('group_address_temperature')
        group_address_setpoint = \
            config.get('group_address_setpoint')
        return cls(xknx,
                   name,
                   group_address_temperature=group_address_temperature,
                   group_address_setpoint=group_address_setpoint)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return self.group_address_temperature == group_address or \
               self.group_address_setpoint == group_address

    @asyncio.coroutine
    def set_internal_setpoint(self, setpoint):
        """Set internal value of setpoint. Call hooks if setpoint was changed."""
        if setpoint != self.setpoint:
            self.setpoint = setpoint
            yield from self.after_update()

    @asyncio.coroutine
    def set_setpoint(self, setpoint):
        """Send setpoint to KNX bus."""
        if not self.supports_setpoint:
            return
        yield from self.send(self.group_address_setpoint,
            DPTArray(DPTTemperature().to_knx(setpoint)))
        yield from self.set_internal_setpoint(setpoint)

    @asyncio.coroutine
    def process(self, telegram):
        """Process incoming telegram."""
        if telegram.group_address == self.group_address_temperature and \
                self.supports_temperature:
            yield from self._process_temperature(telegram)
        elif telegram.group_address == self.group_address_setpoint and \
                self.supports_setpoint:
            yield from self._process_setpoint(telegram)

    @asyncio.coroutine
    def _process_temperature(self, telegram):
        """Process incoming telegram for temperature."""
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 2:
            raise CouldNotParseTelegram()
        self.temperature = DPTTemperature().from_knx(
            (telegram.payload.value[0],
             telegram.payload.value[1]))
        self.last_set = time.time()
        yield from self.after_update()

    @asyncio.coroutine
    def _process_setpoint(self, telegram):
        """Process incoming telegram for setpoint."""
        if not isinstance(telegram.payload, DPTArray) \
                or len(telegram.payload.value) != 2:
            raise CouldNotParseTelegram()
        self.setpoint = DPTTemperature().from_knx(
            (telegram.payload.value[0],
             telegram.payload.value[1]))
        yield from self.after_update()

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        state_addresses = []
        if self.supports_temperature:
            state_addresses.append(self.group_address_temperature)
        if self.supports_setpoint:
            state_addresses.append(self.group_address_setpoint)
        return state_addresses

    def __str__(self):
        """Return object as readable string."""
        last_set_formatted = \
                datetime.datetime.fromtimestamp(
                    self.last_set).strftime('%Y-%m-%d %H:%M:%S') \
                if self.last_set else None
        return '<Climate name="{0}" ' \
               'group_address_temperature="{1}"  ' \
               'group_address_setpoint="{2}" ' \
               'temperature="{3}" last_set="{4}" />' \
               .format(self.name,
                       self.group_address_temperature,
                       self.group_address_setpoint,
                       self.temperature,
                       last_set_formatted)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
