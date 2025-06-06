"""
Module for managing a sensor via KNX.

It provides functionality for

* reading the current state from KNX bus.
* watching for state updates from KNX bus.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from xknx.dpt import DPTBase
from xknx.remote_value import (
    GroupAddressesType,
    RemoteValue,
    RemoteValueSensor,
)
from xknx.typing import DPTParsable

from .device import Device, DeviceCallbackType

if TYPE_CHECKING:
    from xknx.telegram import Telegram
    from xknx.xknx import XKNX


class Sensor(Device):
    """Class for managing a sensor."""

    def __init__(
        self,
        xknx: XKNX,
        name: str,
        group_address_state: GroupAddressesType = None,
        sync_state: bool | int | float | str = True,
        always_callback: bool = False,
        value_type: DPTParsable | type[DPTBase] | None = None,
        device_updated_cb: DeviceCallbackType[Sensor] | None = None,
    ) -> None:
        """Initialize Sensor class."""
        super().__init__(xknx, name, device_updated_cb)
        self.sensor_value = RemoteValueSensor(
            xknx,
            group_address_state=group_address_state,
            sync_state=sync_state,
            value_type=value_type,
            device_name=self.name,
            after_update_cb=self.after_update,
        )
        self.always_callback = always_callback

    def _iter_remote_values(self) -> Iterator[RemoteValue[Any]]:
        """Iterate the devices RemoteValue classes."""
        yield self.sensor_value

    @property
    def last_telegram(self) -> Telegram | None:
        """Return the last telegram received from the RemoteValue."""
        return self.sensor_value.telegram

    def process_group_write(self, telegram: Telegram) -> None:
        """Process incoming and outgoing GROUP WRITE telegram."""
        self.sensor_value.process(telegram, always_callback=self.always_callback)

    def process_group_response(self, telegram: Telegram) -> None:
        """Process incoming GroupValueResponse telegrams."""
        self.sensor_value.process(telegram)

    def unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return self.sensor_value.unit_of_measurement

    def ha_device_class(self) -> str | None:
        """Return the home assistant device class as string."""
        return self.sensor_value.ha_device_class

    def resolve_state(self) -> Any | None:
        """Return the current state of the sensor as a human readable string."""
        return self.sensor_value.value

    def __str__(self) -> str:
        """Return object as readable string."""
        return (
            f'<Sensor name="{self.name}" '
            f"sensor={self.sensor_value.group_addr_str()} "
            f"value={self.resolve_state().__repr__()} "
            f'unit="{self.unit_of_measurement()}"/>'
        )
