"""
Module for managing a switch via KNX.

It provides functionality for

* switching 'on' and 'off'.
* reading the current state from KNX bus.
* reading current power consumption form KNX bus. (DPT 14.056 DPT_Value_Power (W).)
* reading total energy used from KNX bux. (DPT 13.013 DPT_ActiveEnergy_kWh (kWh).)
* reading standby indication of device connected to the switch.
"""
import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, Iterator, Optional

from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueSensor,
    RemoteValueSwitch,
)

from . import BinarySensor, Sensor
from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX

logger = logging.getLogger("xknx.log")


class Switch(Device):
    """Class for managing a switch."""

    def __init__(
        self,
        xknx: "XKNX",
        name: str,
        group_address: Optional[GroupAddressesType] = None,
        group_address_state: Optional[GroupAddressesType] = None,
        group_address_current_power: Optional[GroupAddressesType] = None,
        group_address_total_energy: Optional[GroupAddressesType] = None,
        group_address_standby: Optional[GroupAddressesType] = None,
        invert: bool = False,
        create_sensors: bool = False,
        sync_state: bool = True,
        reset_after: Optional[float] = None,
        device_updated_cb: Optional[DeviceCallbackType] = None,
    ):
        """Initialize Switch class."""
        # pylint: disable=too-many-arguments
        super().__init__(xknx, name, device_updated_cb)

        self.reset_after = reset_after
        self._reset_task: Optional[asyncio.Task[None]] = None

        self.switch = RemoteValueSwitch(
            xknx,
            group_address,
            group_address_state,
            invert=invert,
            device_name=self.name,
            after_update_cb=self.after_update,
        )

        self._current_power = RemoteValueSensor(
            xknx,
            group_address_state=group_address_current_power,
            sync_state=sync_state,
            value_type="power",
            device_name=self.name,
            feature_name="Current power",
            after_update_cb=self.after_update,
        )

        self._total_energy = RemoteValueSensor(
            xknx,
            group_address_state=group_address_total_energy,
            sync_state=sync_state,
            value_type="active_energy_kwh",
            device_name=self.name,
            feature_name="Total energy",
            after_update_cb=self.after_update,
        )

        self._standby = RemoteValueSwitch(
            xknx,
            group_address_state=group_address_standby,
            device_name=self.name,
            feature_name="Standby",
            after_update_cb=self.after_update,
        )

        if create_sensors:
            self.create_sensors()

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any]]:
        """Iterate the devices RemoteValue classes."""
        yield self.switch
        yield self._current_power
        yield self._total_energy
        yield self._standby

    def create_sensors(self) -> None:
        """Create additional sensor devices in xknx."""
        if self._standby.group_address_state is not None:
            BinarySensor(
                self.xknx,
                name=self.name + "_standby",
                group_address_state=self._standby.group_address_state,
            )

        for suffix, group_address, value_type in (
            (
                "_current_power",
                self._current_power.group_address_state,
                "power",
            ),
            (
                "_total_energy",
                self._total_energy.group_address_state,
                "active_energy_kwh",
            ),
        ):
            if group_address is not None:
                Sensor(
                    self.xknx,
                    name=self.name + suffix,
                    group_address_state=group_address,
                    value_type=value_type,
                )

    def __del__(self) -> None:
        """Destructor. Cleaning up if this was not done before."""
        if self._reset_task:
            try:
                self._reset_task.cancel()
            except RuntimeError:
                pass
        super().__del__()

    @classmethod
    def from_config(cls, xknx: "XKNX", name: str, config: Dict[str, Any]) -> "Switch":
        """Initialize object from configuration structure."""
        group_address = config.get("group_address")
        group_address_state = config.get("group_address_state")
        group_address_current_power = config.get("group_address_current_power")
        group_address_total_energy = config.get("group_address_total_energy")
        group_address_standby = config.get("group_address_standby")
        invert = config.get("invert", False)
        reset_after = config.get("reset_after")

        return cls(
            xknx,
            name,
            group_address=group_address,
            group_address_state=group_address_state,
            group_address_current_power=group_address_current_power,
            group_address_total_energy=group_address_total_energy,
            group_address_standby=group_address_standby,
            invert=invert,
            reset_after=reset_after,
        )

    @property
    def state(self) -> Optional[bool]:
        """Return the current switch state of the device."""
        return self.switch.value  # type: ignore

    async def set_on(self) -> None:
        """Switch on switch."""
        await self.switch.on()

    async def set_off(self) -> None:
        """Switch off switch."""
        await self.switch.off()

    @property
    def current_power(self) -> Optional[float]:
        """Return current power usage in W."""
        return self._current_power.value  # type: ignore

    @property
    def total_energy(self) -> Optional[float]:
        """Return total energy usage in kWh."""
        return self._total_energy.value  # type: ignore

    @property
    def standby(self) -> Optional[bool]:
        """Indicate if device connected to the switch is currently in standby."""
        return self._standby.value  # type: ignore

    async def do(self, action: str) -> None:
        """Execute 'do' commands."""
        if action == "on":
            await self.set_on()
        elif action == "off":
            await self.set_off()
        else:
            logger.warning(
                "Could not understand action %s for device %s", action, self.get_name()
            )

    async def process_group_write(self, telegram: "Telegram") -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        if await self.switch.process(telegram):
            if self.reset_after is not None and self.switch.value:
                if self._reset_task:
                    self._reset_task.cancel()
                self._reset_task = asyncio.create_task(
                    self._reset_state(self.reset_after)
                )

    async def _reset_state(self, wait_seconds: float) -> None:
        await asyncio.sleep(wait_seconds)
        await self.set_off()

    def __str__(self) -> str:
        """Return object as readable string."""
        return '<Switch name="{}" switch="{}" current_power="{}" total_energy="{}" standby="{}"/>'.format(
            self.name,
            self.switch.group_addr_str(),
            self._current_power.group_addr_str(),
            self._total_energy.group_addr_str(),
            self._standby.group_addr_str(),
        )
