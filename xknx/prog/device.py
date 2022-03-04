"""This module implements the application layer functionality of a device."""
from __future__ import annotations

import asyncio
from enum import Enum
from typing import TYPE_CHECKING

from xknx.knxip.knxip_enum import CEMIMessageCode

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
    AuthorizeRequest,
    AuthorizeResponse,
    MemoryRead,
    MemoryWrite,
    PropertyValueRead,
    PropertyValueWrite,
    Restart,
)

if TYPE_CHECKING:
    from xknx.xknx import XKNX


class ConnectionState(Enum):
    """Connection State."""

    NOT_CONNECTED = 0
    CONNECTED = 1


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
        self.group_address_type = group_address_type
        self.last_telegram: Telegram | None = None

        self.state = ConnectionState.NOT_CONNECTED
        self.sequence_counter = None

    async def process_telegram(self, telegram: Telegram) -> None:
        """Process a telegram."""
        self.last_telegram = telegram

        print("$$$$$$$$$$$$$$ PROCESS", telegram)
        # TODO Parse Sequence Number!

        if telegram.payload:
            if telegram.payload.CODE == APCIService.DEVICE_DESCRIPTOR_RESPONSE:
                await self.t_ack()
            if telegram.payload.CODE == APCIService.MEMORY_RESPONSE:
                await self.t_ack(self.sequence_counter)
            if telegram.payload.CODE == APCIExtendedService.PROPERTY_VALUE_RESPONSE:
                await self.t_ack(self.sequence_counter)
            if telegram.payload.CODE == APCIExtendedService.AUTHORIZE_RESPONSE:
                await self.t_ack(self.sequence_counter)

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
        
        self.state = ConnectionState.CONNECTED
        self.sequence_counter = -1
        
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

    async def t_ack(self, sequence_number: int | None = None) -> None:
        """Perform a T_ACK."""
        if sequence_number:
            tpdu_type = TPDUType.T_ACK_NUMBERED
        else:
            tpdu_type = TPDUType.T_ACK

        print("$$$$$$$$$$$$$$ PROCESS", sequence_number)

        telegram = Telegram(
            self.ind_add, TelegramDirection.OUTGOING, None, None, tpdu_type
        )
        telegram.sequence_number = sequence_number
        await self.xknx.telegrams.put(telegram)

    async def authorize_request(self, key: int) -> None:
        """Perform a DeviceDescriptor_Read."""
        self.sequence_counter += 1 & 0xF
        telegram = Telegram(
            self.ind_add,
            TelegramDirection.OUTGOING,
            AuthorizeRequest(key, sequence_number=self.sequence_counter),
            priority=Priority.SYSTEM,
        )
        print(">>>", telegram.payload)
        await self.xknx.telegrams.put(telegram)

    async def authorize_request_response(self, key: int) -> None:
        """Process a DeviceDescriptor_Read_Response."""
        await self.authorize_request(key)
        while True:
            await asyncio.sleep(0.1)
            if self.last_telegram:
                if self.last_telegram.payload:
                    if (
                        self.last_telegram.payload.CODE
                        == APCIExtendedService.AUTHORIZE_RESPONSE
                    ):
                        return self.last_telegram.payload.level


    async def devicedescriptor_read(self, descriptor: int) -> None:
        """Perform a DeviceDescriptor_Read."""
        self.sequence_counter += 1 & 0xF
        telegram = Telegram(
            self.ind_add,
            TelegramDirection.OUTGOING,
            DeviceDescriptorRead(descriptor, sequence_number=self.sequence_counter),
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
                        return self.last_telegram.payload.value

    async def memory_read(self, address: int, count: int) -> None:
        """Perform a DeviceDescriptor_Read."""
        self.sequence_counter += 1 & 0xF
        telegram = Telegram(
            self.ind_add,
            TelegramDirection.OUTGOING,
            MemoryRead(address, count, sequence_number=self.sequence_counter),
            priority=Priority.SYSTEM,
        )
        await self.xknx.telegrams.put(telegram)

    async def memory_read_response(self, address: int, count: int) -> None:
        """Process a DeviceDescriptor_Read_Response."""
        await self.memory_read(address, count)
        while True:
            await asyncio.sleep(0.1)
            if self.last_telegram:
                if self.last_telegram.payload:
                    if (
                        self.last_telegram.payload.CODE
                        == APCIService.MEMORY_RESPONSE
                    ):
                        return self.last_telegram

    async def memory_write(self, address: int, data: bytes | None) -> None:
        """Perform a DeviceDescriptor_Read."""
        self.sequence_counter += 1 & 0xF
        telegram = Telegram(
            self.ind_add,
            TelegramDirection.OUTGOING,
            MemoryWrite(address, len(data), data, sequence_number=self.sequence_counter),
            priority=Priority.SYSTEM,
        )
        await self.xknx.telegrams.put(telegram)

    async def memory_write_response(self, address: int, data: bytes | None) -> None:
        """Process a DeviceDescriptor_Read_Response."""
        await self.memory_write(address, data)
        while True:
            await asyncio.sleep(0.1)
            if self.last_telegram:
                if self.last_telegram.payload:
                    if (
                        self.last_telegram.payload.CODE
                        == APCIService.MEMORY_RESPONSE
                    ):
                        return self.last_telegram

    async def propertyvalue_read(
        self,
        object_index: int = 0,
        property_id: int = 0,
        count: int = 0,
        start_index: int = 1) -> None:
        """Perform a PropertyValue_Read."""
        self.sequence_counter += 1 & 0xF
        telegram = Telegram(
            self.ind_add,
            TelegramDirection.OUTGOING,
            PropertyValueRead(object_index, property_id, count, start_index, self.sequence_counter),
            priority=Priority.SYSTEM,
        )
        await self.xknx.telegrams.put(telegram)

    async def propertyvalue_read_response(
        self,
        object_index: int = 0,
        property_id: int = 0,
        count: int = 0,
        start_index: int = 1
    ) -> None:
        """Process a IndividualAddress_Read_Response."""
        await self.propertyvalue_read(object_index, property_id, count, start_index)
        while True:
            await asyncio.sleep(0.1)
            if self.last_telegram:
                if self.last_telegram.payload:
                    if (
                        self.last_telegram.payload.CODE
                        == APCIExtendedService.PROPERTY_VALUE_RESPONSE
                    ):
                        return self.last_telegram.payload.data



    async def propertyvalue_write(
        self,
        object_index: int = 0,
        property_id: int = 0,
        start_index: int = 1,
        data: bytes | None = None) -> None:
        """Perform a PropertyValue_Read."""
        self.sequence_counter += 1 & 0xF
        telegram = Telegram(
            self.ind_add,
            TelegramDirection.OUTGOING,
            PropertyValueWrite(object_index, property_id, 1, start_index, data, self.sequence_counter),
            priority=Priority.SYSTEM,
        )
        await self.xknx.telegrams.put(telegram)

    async def propertyvalue_write_response(
        self,
        object_index: int = 0,
        property_id: int = 0,
        start_index: int = 1,
        data: bytes | None = None
    ) -> None:
        """Process a IndividualAddress_Read_Response."""
        await self.propertyvalue_write(object_index, property_id, start_index, data)
        while True:
            await asyncio.sleep(0.1)
            if self.last_telegram:
                if self.last_telegram.payload:
                    if (
                        self.last_telegram.payload.CODE
                        == APCIExtendedService.PROPERTY_VALUE_RESPONSE
                    ):
                        return self.last_telegram.payload.data


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
                        return self.last_telegram

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
        self.sequence_counter += 1 & 0xF
        telegram = Telegram(
            self.ind_add,
            TelegramDirection.OUTGOING,
            Restart(sequqence_number=self.sequence_counter),
            priority=Priority.SYSTEM,
        )
        await self.xknx.telegrams.put(telegram)
