"""Module for keeping the value of a RemoteValue from KNX bus up to date."""
import asyncio
from enum import Enum

from xknx.exceptions import ConversionError


class StateUpdaterType(Enum):
    """Enum indicating the StateUpdater Type."""

    INIT = 1
    EXPIRE = 2
    PERIODICALLY = 3


class StateUpdater():
    """Class for (periodically) reading the value of a RemoteValue from KNX bus."""

    instances = []

    @classmethod
    def stop_all(cls):
        """Stop all instances of StateUpdater."""
        for state_updater in cls.instances:
            state_updater.stop()

    def __init__(self,
                 xknx,
                 device_name=None,
                 group_address=None,
                 updater_type="EXPIRE",
                 interval_min=60,
                 read_state_awaitable=None):
        """Initialize StateUpdater class."""
        # pylint: disable=too-many-arguments
        try:
            self.updater_type = StateUpdaterType[updater_type.upper()]
        except KeyError:
            raise ConversionError("Invalid state_updater type", updater_type=updater_type, device_name=device_name)
        if interval_min > 1440:
            raise ConversionError("Interval_min to long. Maximum is 1440 minutes (1 day)",
                                  interval_min=interval_min, device_name=device_name)
        self.xknx = xknx
        self.device_name = device_name
        self.group_address = group_address
        self.update_interval = interval_min * 60
        self._rv_read_state = read_state_awaitable
        self._task = None

        self.__class__.instances.append(self)
        self.xknx.loop.create_task(
            self.__async_init())

    def __del__(self):
        """Destructor."""
        self.__class__.instances.remove(self)

    async def __async_init(self):
        """Start StateUpdater - read state on call."""
        await self.xknx.started.wait()
        # TODO: random(1-15) start delay so not all devices are queried at once?
        self.xknx.logger.debug("StateUpdater initializing %s for %s" % (self.group_address, self.device_name))
        if self.updater_type is not StateUpdaterType.INIT:
            self.start()
        await self._rv_read_state(wait_for_result=True)

    def start(self):
        """Start StateUpdater - wait for value to expire."""
        self._task = self.xknx.loop.create_task(
            self._update_loop())

    def stop(self):
        """Stop StateUpdater."""
        if self._task:
            self._task.cancel()
            self._task = None

    def reset(self):
        """Restart the timer."""
        self.stop()
        self.start()

    def update_received(self):
        """Reset the timer if a telegram was received for a "expire" typed StateUpdater."""
        if self.updater_type == StateUpdaterType.EXPIRE:
            self.reset()

    async def _update_loop(self):
        """Wait for the update_interval to expire. Endless loop for updating states."""
        # for StateUpdaterType.EXPIRE:
        #   on successfull read the while loop gets canceled when the callback calls update_received()
        #   when no telegram was received it will try again endlessly
        while True:
            await asyncio.sleep(self.update_interval)
            self._run_callback()

    def _run_callback(self):
        self.xknx.logger.debug("StateUpdater scheduled reading %s for %s" % (self.group_address, self.device_name))
        self.xknx.loop.create_task(self._rv_read_state(wait_for_result=True))
