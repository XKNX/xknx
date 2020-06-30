"""Module for keeping the value of a RemoteValue from KNX bus up to date."""
import asyncio
from enum import Enum
from functools import partial

from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValue


class StateUpdater():
    """Class for keeping the states of RemoteValues up to date."""

    def __init__(self, xknx):
        """Initialize StateUpdater class."""
        self.xknx = xknx
        self.started = False
        self._workers = {}

    def register_remote_value(self, remote_value: RemoteValue):
        """Register a RemoteValue to initialize its state and/or track for expiration."""
        tracker = _StateTracker(
            self.xknx,
            device_name=remote_value.device_name,
            feature_name=remote_value.feature_name,
            group_address=remote_value.group_address_state,
            updater_type="EXPIRE",
            interval_min=5,
            # interval_min=60,
            read_state_awaitable=partial(
                remote_value.read_state, wait_for_result=True))
        self._workers[id(remote_value)] = tracker
        if self.started:
            tracker.start()

    def unregister_remote_value(self, remote_value: RemoteValue):
        """Unregister a RemoteValue from StateUpdater."""
        self._workers.pop(id(remote_value)).stop()

    def update_received(self, remote_value: RemoteValue):
        """Reset the timer when a state update was received."""
        self.xknx.logger.debug("StateUpdater update received for %s" % remote_value)
        if self.started and \
                id(remote_value) in self._workers:
            self._workers[id(remote_value)].update_received()

    def start(self):
        """Start StateUpdater. Initialize states."""
        self.xknx.logger.debug("StateUpdater initializing values")
        self.started = True
        for worker in self._workers.values():
            worker.start()

    def stop(self):
        """Stop StateUpdater."""
        self.xknx.logger.debug("StateUpdater stoping")
        self.started = False
        for worker in self._workers.values():
            worker.stop()


class StateTrackerType(Enum):
    """Enum indicating the StateUpdater Type."""

    INIT = 1
    EXPIRE = 2
    # PERIODICALLY = 3


class _StateTracker():
    """Keeps track of the age of the state from one RemoteValue."""

    # pylint: disable=too-many-instance-attributes
    def __init__(self,
                 xknx,
                 device_name=None,
                 feature_name=None,
                 group_address=None,
                 updater_type="EXPIRE",
                 interval_min=60,
                 read_state_awaitable=None):
        """Initialize StateTracker class."""
        # pylint: disable=too-many-arguments
        try:
            self.updater_type = StateTrackerType[updater_type.upper()]
        except KeyError:
            raise ConversionError("Invalid state_tracker type",
                                  updater_type=updater_type, device_name=device_name, feature_name=feature_name)
        if interval_min > 1440:
            raise ConversionError("Interval_min to long. Maximum is 1440 minutes (1 day)",
                                  interval_min=interval_min, device_name=device_name, feature_name=feature_name)
        self.xknx = xknx
        self.device_name = device_name
        self.feature_name = feature_name
        self.group_address = group_address
        self.update_interval = interval_min * 60
        self._read_state_awaitable = read_state_awaitable
        self._task = None

    def start(self):
        """Start StateTracker - read state on call."""
        self.xknx.logger.debug("StateUpdater initializing %s for %s - %s" %
                               (self.group_address, self.device_name, self.feature_name))
        if self.updater_type is not StateTrackerType.INIT:
            self._start_waiting()
        self._read_state()

    def _start_waiting(self):
        """Start StateTracker - wait for value to expire."""
        self._task = self.xknx.loop.create_task(
            self._update_loop())

    def stop(self):
        """Stop StateTracker."""
        if self._task:
            self._task.cancel()
            self._task = None

    def reset(self):
        """Restart the timer."""
        self.xknx.logger.debug("StateUpdater resetting %s for %s - %s" %
                               (self.group_address, self.device_name, self.feature_name))
        self.stop()
        self._start_waiting()

    def update_received(self):
        """Reset the timer if a telegram was received for a "expire" typed StateUpdater."""
        if self.updater_type == StateTrackerType.EXPIRE:
            self.reset()

    async def _update_loop(self):
        """Wait for the update_interval to expire. Endless loop for updating states."""
        # for StateUpdaterType.EXPIRE:
        #   on successfull read the while loop gets canceled when the callback calls update_received()
        #   when no telegram was received it will try again endlessly
        while True:
            await asyncio.sleep(self.update_interval)
            self._read_state()

    def _read_state(self):
        """Schedule to read the state from the KNX bus."""
        self.xknx.logger.debug("StateUpdater scheduled reading %s for %s - %s" %
                               (self.group_address, self.device_name, self.feature_name))
        self.xknx.loop.create_task(self._read_state_awaitable())
