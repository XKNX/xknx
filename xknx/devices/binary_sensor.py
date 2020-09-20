"""
Module for managing a binary sensor.

A binary sensor can be:
* A switch in the wall (as in the thing you press to switch on the light)
* A motion detector
* A reed sensor for detecting of a window/door is opened or closed.

A BinarySensor may also have Actions attached which are executed after state was changed.
"""
import asyncio
import time

from xknx.remote_value import RemoteValueSwitch

from .action import Action
from .device import Device


class BinarySensor(Device):
    """Class for binary sensor."""

    # pylint: disable=too-many-instance-attributes

    DEFAULT_CONTEXT_TIMEOUT = 1

    def __init__(
        self,
        xknx,
        name,
        group_address_state=None,
        sync_state=True,
        ignore_internal_state=False,
        device_class=None,
        reset_after=None,
        actions=None,
        context_timeout=DEFAULT_CONTEXT_TIMEOUT,
        device_updated_cb=None,
    ):
        """Initialize BinarySensor class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, name, device_updated_cb)
        if actions is None:
            actions = []

        self.actions = actions
        self.device_class = device_class
        self.ignore_internal_state = ignore_internal_state
        self.reset_after = reset_after
        self.state = None

        self._context_timeout = context_timeout
        self._count_set_on = 0
        self._count_set_off = 0
        self._last_set = None
        self._reset_task = None
        self._context_task = None
        # TODO: log a warning if reset_after and sync_state are true ? This could cause actions to self-fire.
        self.remote_value = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_state,
            sync_state=sync_state,
            device_name=self.name,
            # after_update called internally
            after_update_cb=self._state_from_remote_value,
        )

    def _iter_remote_values(self):
        """Iterate the devices RemoteValue classes."""
        yield self.remote_value

    def __del__(self):
        """Destructor. Cleaning up if this was not done before."""
        if self._reset_task:
            self._reset_task.cancel()

        if self._context_task:
            self._context_task.cancel()

    @classmethod
    def from_config(cls, xknx, name, config):
        """Initialize object from configuration structure."""
        group_address_state = config.get("group_address_state")
        context_timeout = config.get("context_timeout", 1)
        sync_state = config.get("sync_state", True)
        device_class = config.get("device_class")
        ignore_internal_state = config.get("ignore_internal_state", False)
        actions = []
        if "actions" in config:
            for action in config["actions"]:
                action = Action.from_config(xknx, action)
                actions.append(action)

        return cls(
            xknx,
            name,
            group_address_state=group_address_state,
            sync_state=sync_state,
            ignore_internal_state=ignore_internal_state,
            context_timeout=context_timeout,
            device_class=device_class,
            actions=actions,
        )

    async def _state_from_remote_value(self):
        """Update the internal state from RemoteValue (Callback)."""
        await self._set_internal_state(self.remote_value.value)

    async def _set_internal_state(self, state):
        """Set the internal state of the device. If state was changed after_update hooks and connected Actions are executed."""
        if state != self.state or self.ignore_internal_state:
            self.state = state
            self.bump_and_get_counter(state)

            if self.ignore_internal_state:
                if self._context_task:
                    self._context_task.cancel()
                self._context_task = self.xknx.loop.create_task(
                    self._counter_task(self._context_timeout)
                )
            else:
                await self._trigger_callbacks()

    async def _counter_task(self, wait_seconds: float):
        """Trigger after 1 second to prevent double triggers."""
        await asyncio.sleep(wait_seconds)
        await self._trigger_callbacks()

        self._count_set_on = 0
        self._count_set_off = 0

        await self.after_update()

    async def _trigger_callbacks(self):
        """Trigger callbacks for device and execute actions if any."""
        await self.after_update()

        for action in self.actions:
            if action.test_if_applicable(self.state, self.counter):
                await action.execute()

    @property
    def counter(self):
        """Return current counter for sensor."""
        return self._count_set_on if self.state else self._count_set_off

    def bump_and_get_counter(self, state):
        """Bump counter and return the number of times a state was set to the same value within CONTEXT_TIMEOUT."""

        def within_same_context():
            """Check if state change was within same context (e.g. 'Button was pressed twice')."""
            if self._last_set is None:
                self._last_set = time.time()
                return False
            new_set_time = time.time()
            time_diff = new_set_time - self._last_set
            self._last_set = new_set_time
            return time_diff < self._context_timeout

        if within_same_context():
            if state:
                self._count_set_on = self._count_set_on + 1
                return self._count_set_on
            self._count_set_off = self._count_set_off + 1
            return self._count_set_off

        if state:
            self._count_set_on = 1
            self._count_set_off = 0
        else:
            self._count_set_on = 0
            self._count_set_off = 1
        return 1

    async def process_group_write(self, telegram):
        """Process incoming GROUP WRITE telegram."""
        if await self.remote_value.process(telegram, always_callback=True):

            if self.reset_after is not None and self.state:
                if self._reset_task:
                    self._reset_task.cancel()
                self._reset_task = self.xknx.loop.create_task(
                    self._reset_state(self.reset_after / 1000)
                )

    async def _reset_state(self, wait_seconds):
        await asyncio.sleep(wait_seconds)
        await self._set_internal_state(False)

    def is_on(self):
        """Return if binary sensor is 'on'."""
        return bool(self.state)

    def is_off(self):
        """Return if binary sensor is 'off'."""
        return not self.state

    def __str__(self):
        """Return object as readable string."""
        return '<BinarySensor name="{}" remote_value="{}" state="{}"/>'.format(
            self.name, self.remote_value.group_addr_str(), self.state
        )
