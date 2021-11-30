"""Module for keeping the value of a RemoteValue from KNX bus up to date."""
from __future__ import annotations

import asyncio
from enum import Enum
import logging
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from xknx.core import XknxConnectionState

if TYPE_CHECKING:
    from xknx.remote_value import RemoteValue
    from xknx.xknx import XKNX


logger = logging.getLogger("xknx.state_updater")

DEFAULT_UPDATE_INTERVAL = 60
MAX_UPDATE_INTERVAL = 1440


class StateUpdater:
    """Class for keeping the state of a RemoteValue up to date."""

    state_updater_semaphore = asyncio.Semaphore(value=2)

    def __init__(
        self,
        xknx: XKNX,
        remote_value: RemoteValue[Any, Any],
        sync_state: bool | int | float | str = True,
    ):
        """Initialize StateUpdater class."""
        self.xknx = xknx
        self.started = False
        self.remote_value = remote_value
        self.initialized = asyncio.Event()
        self.sync_state = sync_state
        self._worker: _StateTracker = self.create_state_tracker()

        self.start()

    @staticmethod
    def parse_tracker_options(
        tracker_options: bool | int | float | str,
        remote_value: RemoteValue[Any, Any],
    ) -> tuple[StateTrackerType, int | float]:
        """Parse tracker type and expiration time."""
        tracker_type = StateTrackerType.EXPIRE
        update_interval: int | float = DEFAULT_UPDATE_INTERVAL

        if isinstance(tracker_options, bool):
            # `True` would be overwritten by the check for `int`
            return (tracker_type, update_interval)
        if isinstance(tracker_options, (int, float)):
            update_interval = tracker_options
        elif isinstance(tracker_options, str):
            _options = tracker_options.split()
            if _options[0].upper() == "INIT":
                tracker_type = StateTrackerType.INIT
            elif _options[0].upper() == "EXPIRE":
                tracker_type = StateTrackerType.EXPIRE
            elif _options[0].upper() == "EVERY":
                tracker_type = StateTrackerType.PERIODICALLY
            else:
                logger.warning(
                    'Could not parse StateUpdater tracker_options "%s" for %s. Using default %s %s minutes.',
                    tracker_options,
                    remote_value,
                    tracker_type,
                    update_interval,
                )
                return (tracker_type, update_interval)
            try:
                if _options[1].isdigit():
                    update_interval = int(_options[1])
            except IndexError:
                pass  # No time given (no _options[1])

        if update_interval > MAX_UPDATE_INTERVAL:
            logger.warning(
                "StateUpdater interval of %s to long for %s. Using maximum of %s minutes (1 day)",
                tracker_options,
                remote_value,
                MAX_UPDATE_INTERVAL,
            )
            update_interval = MAX_UPDATE_INTERVAL
        return (tracker_type, update_interval)

    async def read_state_mutex(self) -> None:
        """Schedule to read the state from the KNX bus - one at a time."""
        async with StateUpdater.state_updater_semaphore:
            # wait until there is nothing else to send to the bus
            await self.xknx.telegram_queue.outgoing_queue.join()
            logger.debug(
                "StateUpdater reading %s for %s - %s",
                self.remote_value.group_address_state,
                self.remote_value.device_name,
                self.remote_value.feature_name,
            )
            # shield from cancellation so update_received() don't cancel the
            # ValueReader leaving the telegram_received_cb until next telegram
            await asyncio.shield(self.remote_value.read_state(wait_for_result=True))

    def create_state_tracker(
        self,
    ) -> _StateTracker:
        """Register a RemoteValue to initialize its state and/or track for expiration."""
        tracker_type, update_interval = StateUpdater.parse_tracker_options(
            self.sync_state, self.remote_value
        )
        return _StateTracker(
            read_state_awaitable=self.read_state_mutex,
            set_initialized_cb=self.set_initialized,
            tracker_type=tracker_type,
            interval_min=update_interval,
        )

    def update_received(self) -> None:
        """Reset the timer when a state update was received."""
        if self.started:
            self._worker.update_received()

    def _start(self) -> None:
        """Start internal StateUpdater. Initialize states."""
        #  dont start if we have no state address
        if not self.remote_value.group_address_state or not self.sync_state:
            self.initialized.set()
            return

        self.started = True
        self._worker.start()

    def set_initialized(self) -> None:
        """Set state to initialised."""
        self.initialized.set()

    def _stop(self) -> None:
        """Stop internal StateUpdater."""
        logger.debug("StateUpdater stopping")
        self.started = False
        self._worker.stop()

    def start(self) -> None:
        """Start StateUpdater."""
        self.xknx.connection_manager.register_connection_state_changed_cb(
            self.connection_state_change_callback
        )

        if self.xknx.connection_manager.state == XknxConnectionState.CONNECTED:
            self._start()

    def stop(self) -> None:
        """Stop StateUpdater."""
        self.xknx.connection_manager.unregister_connection_state_changed_cb(
            self.connection_state_change_callback
        )

        self._stop()

    async def connection_state_change_callback(
        self, state: XknxConnectionState
    ) -> None:
        """Start and stop StateUpdater via connection state update."""
        if state == XknxConnectionState.CONNECTED and not self.started:
            self._start()
        elif (
            state in (XknxConnectionState.DISCONNECTED, XknxConnectionState.CONNECTING)
            and self.started
        ):
            self._stop()


class StateTrackerType(Enum):
    """Enum indicating the StateUpdater Type."""

    INIT = 1
    EXPIRE = 2
    PERIODICALLY = 3


class _StateTracker:
    """Keeps track of the age of the state from one RemoteValue."""

    def __init__(
        self,
        read_state_awaitable: Callable[[], Awaitable[None]],
        set_initialized_cb: Callable[[], None],
        tracker_type: StateTrackerType = StateTrackerType.EXPIRE,
        interval_min: float = 60,
    ):
        """Initialize StateTracker class."""
        self.tracker_type = tracker_type
        self.update_interval = interval_min * 60
        self._mark_as_initialized = set_initialized_cb
        self._read_state = read_state_awaitable
        self._task: asyncio.Task[None] | None = None

    def start(self) -> None:
        """Start StateTracker - read state on call."""
        self.stop()
        self._task = asyncio.create_task(self._start_init())

    async def _start_init(self) -> None:
        """Initialize state, start update loop if appropriate."""
        await self._read_state()
        self._mark_as_initialized()
        if self.tracker_type is not StateTrackerType.INIT:
            self.reset()

    def reset(self) -> None:
        """Start / Restart StateTracker timer - wait for value to expire."""
        self.stop()
        self._task = asyncio.create_task(self._update_loop())

    def stop(self) -> None:
        """Stop StateTracker."""
        if self._task:
            self._task.cancel()
            self._task = None

    def update_received(self) -> None:
        """Reset the timer if a telegram was received for a "expire" typed StateUpdater."""
        if self.tracker_type == StateTrackerType.EXPIRE:
            self.reset()

    async def _update_loop(self) -> None:
        """Wait for the update_interval to expire. Endless loop for updating states."""
        # for StateUpdaterType.EXPIRE:
        #   on successfull read the while loop gets canceled when the callback calls update_received()
        #   when no telegram was received it will try again endlessly
        while True:
            await asyncio.sleep(self.update_interval)
            await self._read_state()
