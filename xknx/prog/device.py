'''
This module implements the application layer functionality of a device.
'''
import asyncio
from enum import Enum

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
    PropertyValueRead,
    Restart,
)


class ConnectionState(Enum):
    NOT_CONNECTED = 0
    A_CONNECTED   = 1


class A_Device:
    '''
    defines a device as programming unit
    '''
    def __init__(self, xknx, ia:IndividualAddress, groupAddressType=GroupAddressType.LONG):
        self.xknx = xknx
        self.ia = ia
        #self.state = ConnectionState.NOT_CONNECTED
        self.groupAddressType = groupAddressType
        self.last_telegram = None

    async def process_telegram(self, telegram):
        self.last_telegram = telegram
        if telegram.payload:
            if telegram.payload.CODE == APCIService.DEVICE_DESCRIPTOR_RESPONSE:
                await self.T_ACK()
            if telegram.payload.CODE == APCIExtendedService.PROPERTY_VALUE_RESPONSE:
                await self.T_ACK(True)


    async def IndividualAddress_Respone(self):
        if self.last_telegram:
            if self.last_telegram.payload.CODE == APCIService.INDIVIDUAL_ADDRESS_RESPONSE:
                return self.last_telegram.source_address
        return None

    async def T_Connect(self):
        telegram = Telegram(
            self.ia,
            TelegramDirection.OUTGOING,
            None,
            None,
            TPDUType.T_CONNECT)
        await self.xknx.telegrams.put(telegram)

    async def T_Connect_Response(self):
        await self.T_Connect()
        while True:
            await asyncio.sleep(0.1)
            if self.last_telegram:
                if self.last_telegram.tpdu_type == TPDUType.T_DISCONNECT:
                    return

    async def T_Disconnect(self):
        telegram = Telegram(
            self.ia,
            TelegramDirection.OUTGOING,
            None,
            None,
            TPDUType.T_DISCONNECT)
        await self.xknx.telegrams.put(telegram)

    async def T_ACK(self, numbered=False):
        if numbered:
            tpdu_type = TPDUType.T_ACK_NUMBERED
        else:
            tpdu_type = TPDUType.T_ACK

        telegram = Telegram(
            self.ia,
            TelegramDirection.OUTGOING,
            None,
            None,
            tpdu_type)
        await self.xknx.telegrams.put(telegram)

    async def DeviceDescriptor_Read(self, descriptor):
        telegram = Telegram(
            self.ia,
            TelegramDirection.OUTGOING,
            DeviceDescriptorRead(descriptor, is_numbered = True),
            priority = Priority.SYSTEM,
            )
        await self.xknx.telegrams.put(telegram)

    async def DeviceDescriptor_Read_Response(self, descriptor):
        await self.DeviceDescriptor_Read(descriptor)
        while True:
            await asyncio.sleep(0.1)
            if self.last_telegram:
                if self.last_telegram.payload:
                    if self.last_telegram.payload.CODE == APCIService.DEVICE_DESCRIPTOR_RESPONSE:
                        return

    async def PropertyValue_Read(self):
        telegram = Telegram(
            self.ia,
            TelegramDirection.OUTGOING,
            PropertyValueRead(0,0x0b,1,1,True,1),
            priority = Priority.SYSTEM,
            )
        await self.xknx.telegrams.put(telegram)

    async def IndividualAddress_Read(self):
        telegram = Telegram(
            GroupAddress(0, self.groupAddressType),
            TelegramDirection.OUTGOING,
            IndividualAddressRead(),
            priority = Priority.SYSTEM,
            )
        await self.xknx.telegrams.put(telegram)

    async def IndividualAddress_Read_Response(self):
        while True:
            await self.IndividualAddress_Read()
            await asyncio.sleep(2)
            if self.last_telegram:
                if self.last_telegram.payload.CODE == APCIService.INDIVIDUAL_ADDRESS_RESPONSE:
                    return self.last_telegram.source_address

    async def IndividualAddress_Write(self):
        telegram = Telegram(
            GroupAddress(0, self.groupAddressType),
            TelegramDirection.OUTGOING,
            IndividualAddressWrite(self.ia),
            priority = Priority.SYSTEM,
            )
        await self.xknx.telegrams.put(telegram)

    async def Restart(self):
        telegram = Telegram(
            self.ia,
            TelegramDirection.OUTGOING,
            Restart(sequqence_number = 2),
            priority = Priority.SYSTEM,
            )
        await self.xknx.telegrams.put(telegram)

    async def test(self):
        await asyncio.sleep(1)
