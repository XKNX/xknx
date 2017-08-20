"""Module for handling commands which may be attached to BinarySensor class."""
import asyncio


class ActionBase():
    """Base Class for handling commands."""

    def __init__(self,
                 xknx,
                 hook="on",
                 counter=1):
        """Initialize Action_Base class."""
        self.xknx = xknx
        self.hook = hook
        self.counter = counter

    def test_counter(self, counter):
        """Test if action filters for specific counter."""
        if self.counter is None:
            # no specific counter_filter -> always true
            return True
        if counter is None:
            return True
        return counter == self.counter

    def test_if_applicable(self, state, counter=None):
        """Test if should be executed for this state and this counter number."""
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

    @asyncio.coroutine
    def execute(self):
        """Execute action. To be overwritten in derived classes."""
        # pylint: disable=no-self-use
        pass

    def __str__(self):
        """Return object as readable string."""
        return '<ActionBase hook="{0}" counter="{1}"/>' \
            .format(self.hook, self.counter)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__


class Action(ActionBase):
    """Class for handling commands."""

    def __init__(self,
                 xknx,
                 hook="on",
                 target=None,
                 method=None,
                 counter=1):
        """Initialize Action class."""
        # pylint: disable=too-many-arguments
        super(Action, self).__init__(xknx, hook, counter)
        self.target = target
        self.method = method

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

    @asyncio.coroutine
    def execute(self):
        """Execute action."""
        yield from self.xknx.devices[self.target].do(self.method)

    def __str__(self):
        """Return object as readable string."""
        return '<Action target="{1}" method="{2}" {3}/>' \
            .format(self.target, self.method, super(Action, self).__str__())


class ActionCallback(ActionBase):
    """Class for handling commands via callbacks."""

    def __init__(self,
                 xknx,
                 callback,
                 hook="on",
                 counter=1):
        """Initialize Action class."""
        # pylint: disable=too-many-arguments
        super(ActionCallback, self).__init__(xknx, hook, counter)
        self.callback = callback

    @asyncio.coroutine
    def execute(self):
        """Execute callback."""
        yield from self.callback()

    def __str__(self):
        """Return object as readable string."""
        return '<ActionCallback callback="{}" {}/>' \
            .format(self.callback.__name__, super(ActionCallback, self).__str__())
