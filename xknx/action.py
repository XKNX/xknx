
class Action():

    def __init__(self,
                 xknx,
                 hook="on",
                 target=None,
                 method=None,
                 counter=1):
        """Initialize Action class."""
        # pylint: disable=too-many-arguments
        self.xknx = xknx
        self.hook = hook
        self.target = target
        self.method = method
        self.counter = counter

    @classmethod
    def from_config(cls, xknx, config):
        """Initialize object from configuration structure."""
        hook = config.get("hook", "on")
        target = config.get("target")
        method = config.get("method")
        counter = config.get("counter", 1)

        return cls(xknx,
                   hook=hook,
                   target=target,
                   method=method,
                   counter=counter)


    def test_counter(self, counter):
        """Test if action filters for specific counter."""
        if self.counter is None:
            # no specific counter_filter -> always true
            return True
        if counter is None:
            return True
        return counter == self.counter


    def test_if_applicable(self, state, counter=None):
        from .binary_sensor import BinarySensorState
        if (state == BinarySensorState.ON) \
                and (self.hook == "on") \
                and self.test_counter(counter):
            return True

        if (state == BinarySensorState.OFF) \
                and (self.hook == "off") \
                and self.test_counter(counter):
            return True

        return False


    def execute(self):
        self.xknx.devices[self.target].do(self.method)


    def __str__(self):
        """Return object as readable string."""
        return '<Action hook="{0}" target="{1}" method="{2}" />' \
            .format(self.hook, self.target, self.method)


    def __eq__(self, other):
        """Equals operator."""
        return self.__dict__ == other.__dict__
