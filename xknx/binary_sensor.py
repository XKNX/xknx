import time
from enum import Enum
from xknx.knx import Address
from .action import Action
from .device import Device
from .exception import CouldNotParseTelegram

# pylint: disable=invalid-name
class BinarySensorState(Enum):
    ON = 1
    OFF = 2


class SwitchTime(Enum):
    SHORT = 1
    LONG = 2


class BinarySensor(Device):

    def __init__(self,
                 xknx,
                 name,
                 group_address=None,
                 device_class=None,
                 significant_bit=1,
                 actions=None,
                 device_updated_cb=None):
        # pylint: disable=too-many-arguments
        Device.__init__(self, xknx, name, device_updated_cb)
        if isinstance(group_address, (str, int)):
            group_address = Address(group_address)
        if not isinstance(significant_bit, int):
            raise TypeError()
        if actions is None:
            actions = []

        self.group_address = group_address
        self.device_class = device_class
        self.significant_bit = significant_bit
        self.state = BinarySensorState.OFF
        self.last_set = None
        self.actions = actions


    @classmethod
    def from_config(cls, xknx, name, config):
        group_address = \
            config.get('group_address')
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
                   device_class=device_class,
                   significant_bit=significant_bit,
                   actions=actions)

    def has_group_address(self, group_address):
        return self.group_address == group_address

    def set_internal_state(self, state):
        if state != self.state:
            self.state = state
            self.after_update()

    def get_switch_time(self):
        if self.last_set is None:
            self.last_set = time.time()
            return SwitchTime.LONG

        new_set_time = time.time()
        time_diff = new_set_time - self.last_set
        self.last_set = new_set_time
        if time_diff < 0.2:
            return SwitchTime.SHORT
        return SwitchTime.LONG


    def process(self, telegram):

        bit_masq = 1 << (self.significant_bit-1)
        binary_value = telegram.payload.value & bit_masq != 0

        if binary_value == 0:
            self.set_internal_state(BinarySensorState.OFF)
        elif binary_value == 1:
            self.set_internal_state(BinarySensorState.ON)
        else:
            raise CouldNotParseTelegram()

        switch_time = self.get_switch_time()

        for action in self.actions:
            if action.test(self.state, switch_time):
                action.execute()


    def is_on(self):
        return self.state == BinarySensorState.ON

    def is_off(self):
        return self.state == BinarySensorState.OFF


    def __str__(self):
        return '<BinarySensor group_address="{0}" name="{1}" state="{2}"/>' \
            .format(self.group_address, self.name, self.state)


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
