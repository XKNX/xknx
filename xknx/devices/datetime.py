"""
Module for broadcasting date/time to the KNX bus.

DateTime is a virtual/pseudo device, using the infrastructure for
beeing configured via xknx.yaml and synchronized periodically
by StateUpdate.
"""

from enum import Enum

from xknx.knx import DPTArray, DPTDate, DPTDateTime, DPTTime, GroupAddress

from .device import Device


class DateTimeBroadcastType(Enum):
    """Enum class for the broadcast type of the enum."""

    DATETIME = 1
    DATE = 2
    TIME = 3


class DateTime(Device):
    """Class for virtual date/time device."""

    # pylint: disable=too-many-arguments
    def __init__(self,
                 xknx,
                 name,
                 broadcast_type=DateTimeBroadcastType.TIME,
                 group_address=None,
                 device_updated_cb=None):
        """Initialize DateTime class."""
        super(DateTime, self).__init__(xknx, name, device_updated_cb)

        self.broadcast_type = broadcast_type

        if isinstance(group_address, (str, int)):
            group_address = GroupAddress(group_address)

        self.group_address = group_address

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        broadcast_type_string = config.get('broadcast_type', 'time').upper()
        broadcast_type = DateTimeBroadcastType[broadcast_type_string]
        group_address = config.get('group_address')
        return cls(xknx,
                   name,
                   broadcast_type=broadcast_type,
                   group_address=group_address)

    def has_group_address(self, group_address):
        """Test if device has given group address."""
        return self.group_address == group_address

    async def broadcast_time(self, response):
        """Broadcast time to KNX bus."""
        if self.broadcast_type == DateTimeBroadcastType.DATETIME:
            broadcast_data = DPTDateTime.current_datetime_as_knx()
            await self.send(
                self.group_address,
                DPTArray(broadcast_data),
                response=response)
        elif self.broadcast_type == DateTimeBroadcastType.DATE:
            broadcast_data = DPTDate.current_date_as_knx()
            await self.send(
                self.group_address,
                DPTArray(broadcast_data),
                response=response)
        elif self.broadcast_type == DateTimeBroadcastType.TIME:
            broadcast_data = DPTTime.current_time_as_knx()
            await self.send(
                self.group_address,
                DPTArray(broadcast_data),
                response=response)

    async def process_group_read(self, telegram):
        """Process incoming GROUP RESPONSE telegram."""
        await self.broadcast_time(True)

    async def sync(self, wait_for_result=True):
        """Read state of device from KNX bus. Used here to broadcast time to KNX bus."""
        await self.broadcast_time(False)

    def __str__(self):
        """Return object as readable string."""
        return '<DateTime name="{0}" group_address="{1}" broadcast_type="{2}" />' \
            .format(self.name, self.group_address.__repr__(), self.broadcast_type.name)

    def __eq__(self, other):
        """Equal operator."""
        return self.__dict__ == other.__dict__
