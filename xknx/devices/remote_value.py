"""
Module for managing a remote value KNX.

Remote value can either be a group address for reading
and and one group address wor writing a KNX value
or a group address for both.
"""
import asyncio
from xknx.knx import Address, DPTBinary, DPTArray
from xknx.exceptions import CouldNotParseTelegram
from xknx.knx import Telegram, DPTScaling


class RemoteValue():
    """Class for managing remlte knx value."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None):
        """Initialize RemoteValue class."""
        self.xknx = xknx
        if isinstance(group_address, (str, int)):
            group_address = Address(group_address)
        if isinstance(group_address_state, (str, int)):
            group_address_state = Address(group_address_state)

        self.group_address = group_address
        self.group_address_state = group_address_state
        self.payload = None

    @property
    def initialized(self):
        """Evaluate if remote value is initialized with group address."""
        return bool(self.group_address_state or self.group_address)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return (self.group_address == group_address) or \
               (self.group_address_state == group_address)

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        if self.group_address_state:
            return [self.group_address_state, ]
        if self.group_address:
            return [self.group_address, ]
        return []

    @staticmethod
    def payload_valid(telegram):
        """Test if telegram payload may be parsed."""
        # pylint: disable=unused-argument
        return True

    @asyncio.coroutine
    def process(self, telegram):
        """Process incoming telegram."""
        if not self.has_group_address(telegram.group_address):
            return False
        if not self.payload_valid(telegram):
            raise CouldNotParseTelegram()
        self.payload = telegram.payload
        return True

    def group_addr_str(self):
        """Return object as readable string."""
        return '{0}/{1}/{2}' \
            .format(self.group_address,
                    self.group_address_state,
                    self.payload)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__

    @asyncio.coroutine
    def send(self, group_address, payload=None):
        """Send payload as telegram to KNX bus."""
        telegram = Telegram()
        telegram.group_address = group_address
        telegram.payload = payload
        yield from self.xknx.telegrams.put(telegram)


class RemoteValueUpDown1008(RemoteValue):
    """Abstraction for remote value of KNX DPT 1.008 / DPT_UpDown."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 invert=False):
        """Initialize remote value of KNX DPT 1.008."""
        super(RemoteValueUpDown1008, self).__init__(xknx, group_address, group_address_state)
        self.invert = invert

    @staticmethod
    def payload_valid(telegram):
        """Test if telegram payload may be parsed."""
        return isinstance(telegram.payload, DPTBinary)

    @asyncio.coroutine
    def down(self):
        """Set value to down."""
        value = 1 if self.invert else 0
        yield from self.send(
            self.group_address,
            DPTBinary(value))

    @asyncio.coroutine
    def up(self):
        """Set value to UP."""
        # pylint: disable=invalid-name
        value = 0 if self.invert else 1
        yield from self.send(
            self.group_address,
            DPTBinary(value))


class RemoteValueStep1007(RemoteValue):
    """Abstraction for remote value of KNX DPT 1.007 / DPT_Step."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 invert=False):
        """Initialize remote value of KNX DPT 1.007."""
        super(RemoteValueStep1007, self).__init__(xknx, group_address, group_address_state)
        self.invert = invert

    @staticmethod
    def payload_valid(telegram):
        """Test if telegram payload may be parsed."""
        return isinstance(telegram.payload, DPTBinary)

    @asyncio.coroutine
    def increase(self):
        """Increase value."""
        value = 1 if self.invert else 0
        yield from self.send(
            self.group_address,
            DPTBinary(value))

    @asyncio.coroutine
    def decrease(self):
        """Decrease the value."""
        value = 0 if self.invert else 1
        yield from self.send(
            self.group_address,
            DPTBinary(value))


class RemoteValueScaling5001(RemoteValue):
    """Abstraction for remote value of KNX DPT 5.001."""

    def __init__(self,
                 xknx,
                 group_address=None,
                 group_address_state=None,
                 invert_scaling=False):
        """Initialize remote value of KNX DPT 5.001."""
        super(RemoteValueScaling5001, self).__init__(xknx, group_address, group_address_state)
        self.state = None
        self.invert_scaling = invert_scaling
        self.payload = DPTArray((0, ))

    @staticmethod
    def payload_valid(telegram):
        """Test if telegram payload may be parsed."""
        return (isinstance(telegram.payload, DPTArray)
                and len(telegram.payload.value) == 1)

    @asyncio.coroutine
    def set(self, scaling):
        """Set new scaling value."""
        if self.invert_scaling:
            scaling = 100 - scaling

        yield from self.send(
            self.group_address,
            DPTArray(DPTScaling.to_knx(scaling)))

    def value(self):
        """Return current scaling value."""
        scaling = DPTScaling.from_knx(self.payload.value)
        if self.invert_scaling:
            scaling = 100 - scaling
        return scaling
