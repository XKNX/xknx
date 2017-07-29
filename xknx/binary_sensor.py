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

class BinarySensor(Device):
    # pylint: disable=too-many-instance-attributes

    CONTEXT_TIMEOUT = 1

    def __init__(self,
                 xknx,
                 name,
                 group_address=None,
                 device_class=None,
                 significant_bit=1,
                 actions=None,
                 device_updated_cb=None):
        """Initialize BinarySensor class."""
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
        self.actions = actions

        self.last_set = None
        self.count_set_on = 0
        self.count_set_off = 0

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
            counter = self.get_counter(state)
            self.after_update()

            for action in self.actions:
                if action.test_if_applicable(self.state, counter):
                    action.execute()

    def get_counter(self, state):
        """
        Returns the number of times a state was set to the same
        value within CONTEXT_TIMEOUT.
        Untechnically: Returns how often a button was pressed
        """
        def within_same_context():
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
            else:
                self.count_set_off = self.count_set_off + 1
                return self.count_set_off
        else:
            if state == BinarySensorState.ON:
                self.count_set_on = 1
                self.count_set_off = 0
            else:
                self.count_set_on = 0
                self.count_set_off = 1
            return 1

    def process(self, telegram):
        """Process incoming telegram."""
        bit_masq = 1 << (self.significant_bit-1)
        binary_value = telegram.payload.value & bit_masq != 0

        if binary_value == 0:
            self.set_internal_state(BinarySensorState.OFF)
        elif binary_value == 1:
            self.set_internal_state(BinarySensorState.ON)
        else:
            raise CouldNotParseTelegram()



    def is_on(self):
        return self.state == BinarySensorState.ON

    def is_off(self):
        return self.state == BinarySensorState.OFF


    def __str__(self):
        """Return object as readable string."""
        return '<BinarySensor group_address="{0}" name="{1}" state="{2}"/>' \
            .format(self.group_address, self.name, self.state)


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
