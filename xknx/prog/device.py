"""This module implements the application layer functionality of a device."""
from __future__ import annotations

import asyncio
from enum import Enum
from typing import TYPE_CHECKING

from xknx.telegram import (
    IndividualAddress,
    Priority,
    Telegram,
    TelegramDirection,
    TPDUType,
)
from xknx.telegram.address import GroupAddress, GroupAddressType
from xknx.telegram.apci import (
    APCIExtendedService,
    APCIService,
    DeviceDescriptorRead,
    IndividualAddressRead,
    IndividualAddressWrite,
    MemoryRead,
    PropertyValueRead,
    Restart,
)

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class ConnectionState(Enum):
    """Connection State."""

    NOT_CONNECTED = 0
    A_CONNECTED = 1


class ProgDevice:
    """This Class defines a device as programming unit (A_Device)."""

    def __init__(
        self,
        xknx: XKNX,
        ind_add: IndividualAddress,
        group_address_type: GroupAddressType = GroupAddressType.LONG,
    ):
        """Init this class."""
        self.xknx = xknx
        self.ind_add = ind_add
        # self.state = ConnectionState.NOT_CONNECTED
        self.group_address_type = group_address_type
        self.last_telegram: Telegram | None = None

    async def process_telegram(self, telegram: Telegram) -> None:
        """Process a telegram."""
        self.last_telegram = telegram
        if telegram.payload:
            if telegram.payload.CODE == APCIService.DEVICE_DESCRIPTOR_RESPONSE:
                await self.t_ack()
            if telegram.payload.CODE == APCIExtendedService.PROPERTY_VALUE_RESPONSE:
                await self.t_ack(True)

    async def individualaddress_respone(self) -> IndividualAddress | None:
        """Process a IndividualAddress_Respone."""
        if self.last_telegram:
            if self.last_telegram.payload:
                if (
                    self.last_telegram.payload.CODE
                    == APCIService.INDIVIDUAL_ADDRESS_RESPONSE
                ):
                    return self.last_telegram.source_address
        return None

    async def t_connect(self) -> None:
        """Perform a T_Connect."""
        telegram = Telegram(
            self.ind_add, TelegramDirection.OUTGOING, None, None, TPDUType.T_CONNECT
        )
        await self.xknx.telegrams.put(telegram)

    async def t_connect_response(self) -> None:
        """Process a T_Connect_Response."""
        await self.t_connect()
        while True:
            await asyncio.sleep(0.1)
            if self.last_telegram:
                if self.last_telegram.tpdu_type == TPDUType.T_DISCONNECT:
                    return

    async def t_disconnect(self) -> None:
        """Perform a T_Disconnect."""
        telegram = Telegram(
            self.ind_add, TelegramDirection.OUTGOING, None, None, TPDUType.T_DISCONNECT
        )
        await self.xknx.telegrams.put(telegram)

    async def t_ack(self, numbered: bool = False) -> None:
        """Perform a T_ACK."""
        if numbered:
            tpdu_type = TPDUType.T_ACK_NUMBERED
        else:
            tpdu_type = TPDUType.T_ACK

        telegram = Telegram(
            self.ind_add, TelegramDirection.OUTGOING, None, None, tpdu_type
        )
        await self.xknx.telegrams.put(telegram)

    async def devicedescriptor_read(self, descriptor: int) -> None:
        """Perform a DeviceDescriptor_Read."""
        telegram = Telegram(
            self.ind_add,
            TelegramDirection.OUTGOING,
            DeviceDescriptorRead(descriptor, is_numbered=True),
            priority=Priority.SYSTEM,
        )
        await self.xknx.telegrams.put(telegram)

    async def devicedescriptor_read_response(self, descriptor: int) -> None:
        """Process a DeviceDescriptor_Read_Response."""
        await self.devicedescriptor_read(descriptor)
        while True:
            await asyncio.sleep(0.1)
            if self.last_telegram:
                if self.last_telegram.payload:
                    if (
                        self.last_telegram.payload.CODE
                        == APCIService.DEVICE_DESCRIPTOR_RESPONSE
                    ):
                        return

    async def propertyvalue_read(self) -> None:
        """Perform a PropertyValue_Read."""
        telegram = Telegram(
            self.ind_add,
            TelegramDirection.OUTGOING,
            PropertyValueRead(0, 0x0B, 1, 1, True, 1),
            priority=Priority.SYSTEM,
        )
        await self.xknx.telegrams.put(telegram)

    async def memory_read(self, address: int = 0, count: int = 0) -> None:
        """Perform a PropertyValue_Read."""
        telegram = Telegram(
            self.ind_add,
            TelegramDirection.OUTGOING,
            MemoryRead(address, count),
            priority=Priority.SYSTEM,
        )
        await self.xknx.telegrams.put(telegram)

    async def individualaddress_read(self) -> None:
        """Perform a IndividualAddress_Read."""
        telegram = Telegram(
            GroupAddress(0, self.group_address_type),
            TelegramDirection.OUTGOING,
            IndividualAddressRead(),
            priority=Priority.SYSTEM,
        )
        await self.xknx.telegrams.put(telegram)

    async def individualaddress_read_response(self) -> IndividualAddress | None:
        """Process a IndividualAddress_Read_Response."""
        while True:
            await self.individualaddress_read()
            await asyncio.sleep(2)
            if self.last_telegram:
                if self.last_telegram.payload:
                    if (
                        self.last_telegram.payload.CODE
                        == APCIService.INDIVIDUAL_ADDRESS_RESPONSE
                    ):
                        return self.last_telegram.source_address

    async def individualaddress_write(self) -> None:
        """Perform a IndividualAddress_Write."""
        telegram = Telegram(
            GroupAddress(0, self.group_address_type),
            TelegramDirection.OUTGOING,
            IndividualAddressWrite(self.ind_add),
            priority=Priority.SYSTEM,
        )
        await self.xknx.telegrams.put(telegram)

    async def restart(self) -> None:
        """Perform a Restart."""
        telegram = Telegram(
            self.ind_add,
            TelegramDirection.OUTGOING,
            Restart(sequqence_number=2),
            priority=Priority.SYSTEM,
        )
        await self.xknx.telegrams.put(telegram)
