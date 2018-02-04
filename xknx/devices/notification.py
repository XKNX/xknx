"""Module for managing a notification via KNX."""
from xknx.exceptions import CouldNotParseTelegram
from xknx.knx import DPTArray, DPTString, GroupAddress

from .device import Device


class Notification(Device):
    """Class for managing a notification."""

    def __init__(self,
                 xknx,
                 name,
                 group_address=None,
                 device_updated_cb=None):
        """Initialize notification class."""
        # pylint: disable=too-many-arguments
        super(Notification, self).__init__(xknx, name, device_updated_cb)
        if isinstance(group_address, (str, int)):
            group_address = GroupAddress(group_address)

        self.group_address = group_address
        self.message = ""

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address = \
            config.get('group_address')

        return cls(xknx,
                   name,
                   group_address=group_address)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return self.group_address == group_address

    def __str__(self):
        """Return object as readable string."""
        return '<Notification name="{0}" ' \
            'group_address="{1}" ' \
            'message="{2}" />' \
            .format(
                self.name,
                self.group_address,
                self.message)

    async def _set_internal_message(self, message):
        """Set the internal state of the device. If state was changed after update hooks are executed."""
        if message != self.message:
            self.message = message
            await self.after_update()

    async def set(self, message):
        """Set message."""
        cropped_message = message[:14]
        await self.send(self.group_address, DPTArray(DPTString().to_knx(cropped_message)))
        await self._set_internal_message(cropped_message)

    async def do(self, action):
        """Execute 'do' commands."""
        if action.startswith("message:"):
            await self.set(action[8:])
        else:
            self.xknx.logger.warning("Could not understand action %s for device %s", action, self.get_name())

    def state_addresses(self):
        """Return group addresses which should be requested to sync state."""
        return [self.group_address, ]

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        if telegram.group_address == self.group_address:
            await self._process_message(telegram)

    async def _process_message(self, telegram):
        """Process incoming telegram for on/off state."""
        if not isinstance(telegram.payload, DPTArray):
            raise CouldNotParseTelegram(
                "payload not of type DPTArray",
                payload=telegram.payload,
                device_name=self.name)
        if len(telegram.payload.value) != 14:
            raise CouldNotParseTelegram(
                "payload has invalid length!=14",
                length=len(telegram.payload.value), device_name=self.name)
        await self._set_internal_message(DPTString().from_knx(telegram.payload.value))

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
