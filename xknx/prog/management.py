"""This modul implements the management procedures as described in KNX-Standard 3.5.2."""
from __future__ import annotations

import asyncio

from typing import (
    TYPE_CHECKING,
)

from xknx.telegram.address import GroupAddress, IndividualAddress
from xknx.prog.device import ProgDevice

if TYPE_CHECKING:
    from device import Device
    from xknx.xknx import XKNX
    from xknx.telegram import Telegram


NM_OK = 0
NM_EXISTS = 1
NM_TIME_OUT = 2


class NetworkManagement:
    """Class for network management functionality."""

    def __init__(self, xknx: XKNX):
        """Construct NM instance."""
        self.xknx = xknx
        xknx.telegram_queue.register_telegram_received_cb(
            self.telegram_received_cb
        )
        # map for registered devices
        self.reg_dev: dict[IndividualAddress, Device] = {}

    async def telegram_received_cb(self, tele: Telegram) -> None:
        """Do something with the received telegram."""
        if tele.source_address in self.reg_dev:
            await self.reg_dev[tele.source_address].process_telegram(tele)
        if tele.destination_address == GroupAddress("0"):
            for reg_dev_val in self.reg_dev.values():
                await reg_dev_val.process_telegram(tele)

    async def individualaddress_write(self, ind_add: IndividualAddress) -> int:
        """Perform IndividualAdress_Write."""
        device = ProgDevice(self.xknx, ind_add)
        self.reg_dev[ind_add] = device

        # chech if IA is already present
        try:
            await asyncio.wait_for(device.t_connect_response(), 0.5)
            return NM_EXISTS
        except asyncio.TimeoutError:
            pass

        try:
            await asyncio.wait_for(device.devicedescriptor_read_response(0), 0.5)
            await device.t_disconnect()
            return NM_EXISTS
        except asyncio.TimeoutError:
            pass

        # wait until PROG button is pressed
        try:
            await asyncio.wait_for(device.individualaddress_read_response(), 600)
        except asyncio.TimeoutError:
            return NM_TIME_OUT

        await device.individualaddress_write()

        # Zusatz ETS reengeneering
        await device.t_connect()
        try:
            await asyncio.wait_for(device.devicedescriptor_read_response(0), 1.0)
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {ind_add}")

        await device.propertyvalue_read()
        await device.restart()
        await asyncio.sleep(1)
        await device.t_disconnect()
        return NM_OK
