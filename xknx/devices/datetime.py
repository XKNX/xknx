"""
Module for broadcasting date/time to the KNX bus.

DateTime is a virtual/pseudo device, using the infrastructure for
beeing configured via xknx.yaml and synchronized periodically
by StateUpdate.
"""
import asyncio
import time

from xknx.remote_value import RemoteValueDateTime

from .device import Device


class DateTime(Device):
    """Class for virtual date/time device."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        xknx,
        name: str,
        broadcast_type: str = "TIME",
        localtime: bool = True,
        group_address=None,
        device_updated_cb=None,
    ):
        """Initialize DateTime class."""
        super().__init__(xknx, name, device_updated_cb)
        self.localtime = localtime
        self._broadcast_type = broadcast_type.upper()
        self._remote_value = RemoteValueDateTime(
            xknx,
            group_address=group_address,
            sync_state=False,
            value_type=broadcast_type,
            device_name=name,
            after_update_cb=self.after_update,
        )
        self._broadcast_task = self._create_broadcast_task(minutes=60)

    def __del__(self):
        """Destructor. Cleaning up if this was not done before."""
        if self._broadcast_task:
            self._broadcast_task.cancel()

    def _iter_remote_values(self):
        """Iterate the devices RemoteValue classes."""
        yield self._remote_value

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        broadcast_type = config.get("broadcast_type", "time").upper()
        group_address = config.get("group_address")
        return cls(
            xknx, name, broadcast_type=broadcast_type, group_address=group_address
        )

    def _create_broadcast_task(self, minutes: int = 60):
        """Create an asyncio.Task for broadcasting local time periodically if `localtime` is set."""

        async def broadcast_loop(self, minutes: int):
            """Endless loop for broadcasting local time."""
            while True:
                await self.broadcast_localtime()
                await asyncio.sleep(minutes * 60)

        if self.localtime:
            loop = asyncio.get_event_loop()
            return loop.create_task(broadcast_loop(self, minutes=minutes))
        return None

    async def broadcast_localtime(self, response=False):
        """Broadcast the local time to KNX bus."""
        await self._remote_value.set(time.localtime(), response=response)

    async def set(self, struct_time: time.struct_time):
        """Set time and send to KNX bus."""
        await self._remote_value.set(struct_time)

    async def process_group_read(self, telegram):
        """Process incoming GROUP READ telegram."""
        if self.localtime:
            await self.broadcast_localtime(True)
        else:
            await self._remote_value.respond()

    async def sync(self, wait_for_result=False):
        """Read state of device from KNX bus. Used here to broadcast time to KNX bus."""
        if self.localtime:
            await self.broadcast_localtime(response=False)

    def __str__(self):
        """Return object as readable string."""
        return '<DateTime name="{}" group_address="{}" broadcast_type="{}" />'.format(
            self.name, self._remote_value.group_addr_str(), self._broadcast_type
        )
