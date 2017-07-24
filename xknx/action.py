from .switchtime import SwitchTime
from .binaryinput import BinaryInputState

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
        return '<Action hook="{0}" target="{1}" method="{2}" />' \
            .format(self.hook, self.target, self.method)


    def __eq__(self, other):
        return self.__dict__ == other.__dict__
