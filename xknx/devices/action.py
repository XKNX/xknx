"""Module for handling commands which may be attached to BinarySensor class."""


class ActionBase:
    """Base Class for handling commands."""

    def __init__(self, xknx, hook="on", counter=1):
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
        if state and (self.hook == "on"):
            return self.test_counter(counter)
        if not state and (self.hook == "off"):
            return self.test_counter(counter)
        return False

    async def execute(self):
        """Execute action. To be overwritten in derived classes."""
        self.xknx.logger.info("Execute not implemented for %s", self.__class__.__name__)

    def __str__(self):
        """Return object as readable string."""
        return f'<ActionBase hook="{self.hook}" counter="{self.counter}"/>'

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__


class Action(ActionBase):
    """Class for handling commands."""

    def __init__(self, xknx, hook="on", target=None, method=None, counter=1):
        """Initialize Action class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, hook, counter)
        self.target = target
        self.method = method

    @classmethod
    def from_config(cls, xknx, config):
        """Initialize object from configuration structure."""
        hook = config.get("hook", "on")
        target = config.get("target")
        method = config.get("method")
        counter = config.get("counter", 1)
        return cls(xknx, hook=hook, target=target, method=method, counter=counter)

    async def execute(self):
        """Execute action."""
        if self.target is not None:
            if self.target not in self.xknx.devices:
                self.xknx.logger.warning(
                    "Unknown device %s witin action %s.", self.target, self
                )
                return
            await self.xknx.devices[self.target].do(self.method)

    def __str__(self):
        """Return object as readable string."""
        return '<Action target="{}" method="{}" {}/>'.format(
            self.target, self.method, super().__str__()
        )


class ActionCallback(ActionBase):
    """Class for handling commands via callbacks."""

    def __init__(self, xknx, callback, hook="on", counter=1):
        """Initialize Action class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, hook, counter)
        self.callback = callback

    async def execute(self):
        """Execute callback."""
        await self.callback()

    def __str__(self):
        """Return object as readable string."""
        return '<ActionCallback callback="{}" {}/>'.format(
            self.callback.__name__, super().__str__()
        )
