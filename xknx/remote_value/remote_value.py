"""
Module for managing a remote value on the KNX bus.

Remote value can be :
- a group address for writing a KNX value,
- a group address for reading a KNX value,
- or a group of both representing the same value.
"""
import logging

from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram, TelegramType

logger = logging.getLogger("xknx.log")


class RemoteValue:
    """Class for managing remote knx value."""

    # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        xknx,
        group_address=None,
        group_address_state=None,
        sync_state=True,
        device_name=None,
        feature_name=None,
        after_update_cb=None,
    ):
        """Initialize RemoteValue class."""
        # pylint: disable=too-many-arguments
        self.xknx = xknx
        if group_address is not None:
            group_address = GroupAddress(group_address)
        if group_address_state is not None:
            group_address_state = GroupAddress(group_address_state)

        self.group_address = group_address
        self.group_address_state = group_address_state
        self.device_name = "Unknown" if device_name is None else device_name
        self.feature_name = "Unknown" if feature_name is None else feature_name
        self.after_update_cb = after_update_cb
        self.payload = None

        if sync_state and self.group_address_state:
            self.xknx.state_updater.register_remote_value(
                self, tracker_options=sync_state
            )

    def __del__(self):
        """Destructor. Removing self from StateUpdater if was registered."""
        try:
            self.xknx.state_updater.unregister_remote_value(self)
        except KeyError:
            pass

    @property
    def initialized(self):
        """Evaluate if remote value is initialized with group address."""
        return bool(self.group_address_state or self.group_address)

    @property
    def readable(self):
        """Evaluate if remote value should be read from bus."""
        return bool(self.group_address_state)

    @property
    def writable(self):
        """Evaluate if remote value has a group_address set."""
        return bool(self.group_address)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return group_address in [self.group_address, self.group_address_state]

    def payload_valid(self, payload):
        """Test if telegram payload may be parsed - to be implemented in derived class.."""
        # pylint: disable=unused-argument
        logger.warning(
            "'payload_valid()' not implemented for %s", self.__class__.__name__
        )
        return True

    def from_knx(self, payload):
        """Convert current payload to value - to be implemented in derived class."""
        # pylint: disable=unused-argument
        logger.warning("'from_knx()' not implemented for %s", self.__class__.__name__)

    def to_knx(self, value):
        """Convert value to payload - to be implemented in derived class."""
        # pylint: disable=unused-argument
        logger.warning("'to_knx()' not implemented for %s", self.__class__.__name__)

    async def process(self, telegram, always_callback=False):
        """Process incoming telegram."""
        if not self.has_group_address(telegram.group_address):
            return False
        if not self.payload_valid(telegram.payload):
            raise CouldNotParseTelegram(
                "payload invalid",
                payload=telegram.payload,
                group_address=telegram.group_address,
                device_name=self.device_name,
                feature_name=self.feature_name,
            )
        self.xknx.state_updater.update_received(self)
        if self.payload is None or always_callback or self.payload != telegram.payload:
            self.payload = telegram.payload
            if self.after_update_cb is not None:
                await self.after_update_cb()
        return True

    @property
    def value(self):
        """Return current value."""
        if self.payload is None:
            return None
        return self.from_knx(self.payload)

    async def _send(self, payload, response=False):
        """Send payload as telegram to KNX bus."""
        telegram = Telegram(
            group_address=self.group_address,
            telegramtype=(
                TelegramType.GROUP_RESPONSE if response else TelegramType.GROUP_WRITE
            ),
            payload=payload,
        )
        await self.xknx.telegrams.put(telegram)

    async def set(self, value, response=False):
        """Set new value."""
        if not self.initialized:
            logger.info(
                "Setting value of uninitialized device: %s - %s (value: %s)",
                self.device_name,
                self.feature_name,
                value,
            )
            return
        if not self.writable:
            logger.warning(
                "Attempted to set value for non-writable device: %s - %s (value: %s)",
                self.device_name,
                self.feature_name,
                value,
            )
            return

        payload = self.to_knx(value)  # pylint: disable=assignment-from-no-return
        await self._send(payload, response)
        # self.payload is set and after_update_cb() called when the outgoing telegram is processed.

    async def respond(self):
        """Send current payload as GroupValueResponse telegram to KNX bus."""
        if self.payload is not None:
            await self._send(self.payload, response=True)

    async def read_state(self, wait_for_result=False):
        """Send GroupValueRead telegram for state address to KNX bus."""
        if self.readable:
            logger.debug("Sync %s - %s", self.device_name, self.feature_name)
            # pylint: disable=import-outside-toplevel
            # TODO: send a ReadRequset and start a timeout from here instead of ValueReader
            #       cancel timeout form process(); delete ValueReader
            from xknx.core import ValueReader

            value_reader = ValueReader(self.xknx, self.group_address_state)
            if wait_for_result:
                telegram = await value_reader.read()
                if telegram is not None:
                    await self.process(telegram)
                else:
                    logger.warning(
                        "Could not sync group address '%s' (%s - %s)",
                        self.group_address_state,
                        self.device_name,
                        self.feature_name,
                    )
            else:
                await value_reader.send_group_read()

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return None

    def group_addr_str(self):
        """Return object as readable string."""
        return "{}/{}/{}/{}".format(
            self.group_address.__repr__(),
            self.group_address_state.__repr__(),
            self.payload,
            self.value,
        )

    def __str__(self):
        """Return object as string representation."""
        return '<{} device_name="{}" feature_name="{}" {}/>'.format(
            self.__class__.__name__,
            self.device_name,
            self.feature_name,
            self.group_addr_str(),
        )

    def __eq__(self, other):
        """Equal operator."""
        for key, value in self.__dict__.items():
            if key == "after_update_cb":
                continue
            if key not in other.__dict__:
                return False
            if other.__dict__[key] != value:
                return False
        for key, value in other.__dict__.items():
            if key == "after_update_cb":
                continue
            if key not in self.__dict__:
                return False
        return True
