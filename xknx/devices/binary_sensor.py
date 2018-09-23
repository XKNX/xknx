"""
Module for managing a binary sensor.

A binary sensor can be:
* A switch in the wall (as in the thing you press to switch on the light)
* A motion detector
* A reed sensor for detecting of a window/door is opened or closed.

A BinarySensor may also have Actions attached which are executed after state was changed.
"""
import asyncio
import time
from enum import Enum

from xknx.exceptions import CouldNotParseTelegram
from xknx.knx import DPTBinary, GroupAddress

from .action import Action
from .device import Device


# pylint: disable=invalid-name
class BinarySensorState(Enum):
    """Enum class for the state of a binary sensor."""

    ON = 1
    OFF = 2


class BinarySensor(Device):
    """Class for binary sensor."""

    # pylint: disable=too-many-instance-attributes

    CONTEXT_TIMEOUT = 1

    def __init__(self,
                 xknx,
                 name,
                 group_address=None,
                 group_address_state=None,
                 device_class=None,
                 significant_bit=1,
                 reset_after=None,
                 actions=None,
                 device_updated_cb=None):
        """Initialize BinarySensor class."""
        # pylint: disable=too-many-arguments
        super(BinarySensor, self).__init__(xknx, name, device_updated_cb)
        if isinstance(group_address, (str, int)):
            group_address = GroupAddress(group_address)
        if isinstance(group_address_state, (str, int)):
            group_address_state = GroupAddress(group_address_state)
        if not isinstance(significant_bit, int):
            raise TypeError()
        if actions is None:
            actions = []

        self.group_address = group_address
        self.group_address_state = group_address_state
        self.device_class = device_class
        self.significant_bit = significant_bit
        self.reset_after = reset_after
        self.state = BinarySensorState.OFF
        self.actions = actions

        self.last_set = None
        self.count_set_on = 0
        self.count_set_off = 0

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address = \
            config.get('group_address')
        group_address_state = \
            config.get('group_address_state')
        device_class = \
            config.get('device_class')
        significant_bit = \
            config.get('significant_bit', 1)

        actions = []
        if "actions" in config:
            for action in config["actions"]:
                action = Action.from_config(xknx, action)
                actions.append(action)

        return cls(xknx,
                   name,
                   group_address=group_address,
                   group_address_state=group_address_state,
                   device_class=device_class,
                   significant_bit=significant_bit,
                   actions=actions)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return group_address in [self.group_address, self.group_address_state]

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        return [self.group_address_state, ]

    async def _set_internal_state(self, state):
        """Set the internal state of the device. If state was changed after update hooks and connected Actions are executed."""
        if state != self.state:
            self.state = state
            counter = self.bump_and_get_counter(state)
            await self.after_update()

            for action in self.actions:
                if action.test_if_applicable(self.state, counter):
                    await action.execute()

    def bump_and_get_counter(self, state):
        """Bump counter and return the number of times a state was set to the same value within CONTEXT_TIMEOUT."""
        def within_same_context():
            """Check if state change was within same context (e.g. 'Button was pressed twice')."""
            if self.last_set is None:
                self.last_set = time.time()
                return False
            new_set_time = time.time()
            time_diff = new_set_time - self.last_set
            self.last_set = new_set_time
            return time_diff < self.CONTEXT_TIMEOUT

        if within_same_context():
            if state == BinarySensorState.ON:
                self.count_set_on = self.count_set_on + 1
                return self.count_set_on
            self.count_set_off = self.count_set_off + 1
            return self.count_set_off

        if state == BinarySensorState.ON:
            self.count_set_on = 1
            self.count_set_off = 0
        else:
            self.count_set_on = 0
            self.count_set_off = 1
        return 1

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        if not isinstance(telegram.payload, DPTBinary):
            raise CouldNotParseTelegram("invalid payload", payload=telegram.payload, device_name=self.name)

        bit_masq = 1 << (self.significant_bit-1)
        if telegram.payload.value & bit_masq == 0:
            await self._set_internal_state(BinarySensorState.OFF)
        else:
            await self._set_internal_state(BinarySensorState.ON)
            if self.reset_after is not None:
                await asyncio.sleep(self.reset_after/1000)
                await self._set_internal_state(BinarySensorState.OFF)

    def is_on(self):
        """Return if binary sensor is 'on'."""
        return self.state == BinarySensorState.ON

    def is_off(self):
        """Return if binary sensor is 'off'."""
        return self.state == BinarySensorState.OFF

    def __str__(self):
        """Return object as readable string."""
        return '<BinarySensor group_address="{0}" name="{1}" state="{2}"/>' \
            .format(self.group_address.__repr__(), self.name, self.state)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
