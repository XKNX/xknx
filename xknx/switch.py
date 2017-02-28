import time
from enum import Enum
from xknx.knx import Address
from .binaryinput import BinaryInput, BinaryInputState

class SwitchTime(Enum):
    SHORT = 1
    LONG = 2

class Action():

    def __init__(self,
                 xknx,
                 hook=None,
                 target=None,
                 method=None,
                 switch_time=None):
        # pylint: disable=too-many-arguments
        self.xknx = xknx
        self.hook = hook
        self.target = target
        self.method = method
        self.switch_time = switch_time


    @classmethod
    def from_config(cls, xknx, config):
        hook = config.get("hook")
        target = config.get("target")
        method = config.get("method")

        def get_switch_time_from_config(config):
            if "switch_time" in config:
                if config["switch_time"] == "long":
                    return SwitchTime.LONG
                elif config["switch_time"] == "short":
                    return SwitchTime.SHORT
            return None
        switch_time = get_switch_time_from_config(config)

        return cls(xknx,
                   hook=hook,
                   target=target,
                   method=method,
                   switch_time=switch_time)


    def test_switch_time(self, switch_time):
        if switch_time is not None:
            # no specific switch_time -> always true
            return True

        return switch_time == self.switch_time


    def test(self, state, switch_time):
        if (state == BinaryInputState.ON) \
                and (self.hook == "on") \
                and self.test_switch_time(switch_time):
            return True

        if (state == BinaryInputState.OFF) \
                and (self.hook == "off") \
                and self.test_switch_time(switch_time):
            return True

        return False


    def execute(self):
        self.xknx.devices[self.target].do(self.method)


    def __str__(self):
        return "<Action hook={0} target={1} method={2}>" \
            .format(self.hook, self.target, self.method)


    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Switch(BinaryInput):

    def __init__(self,
                 xknx,
                 name,
                 group_address=None,
                 actions=None):

        if isinstance(group_address, (str, int)):
            group_address = Address(group_address)
        if actions is None:
            actions = []

        BinaryInput.__init__(self, xknx, name, group_address)
        self.last_set = None
        self.actions = actions


    @classmethod
    def from_config(cls, xknx, name, config):
        group_address = \
            config.get('group_address')

        actions = []
        if "actions" in config:
            for action in config["actions"]:
                action = Action.from_config(xknx, action)
                actions.append(action)

        return cls(xknx,
                   name,
                   group_address=group_address,
                   actions=actions)


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
        BinaryInput.process(self, telegram)
        switch_time = self.get_switch_time()

        for action in self.actions:
            if action.test(self.state, switch_time):
                action.execute()


    def __str__(self):
        return "<Switch group_address={0}, name={1}>" \
            .format(self.group_address, self.name)


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
