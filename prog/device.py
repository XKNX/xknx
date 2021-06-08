'''
This module implements the application layer functionality of a device.
'''
from enum import Enum

from xknx.telegram import Telegram, TelegramDirection, IndividualAddress,TPDUType
#from xknx.io import Connect
#from xknx.knxip import ConnectRequestType
#from xknx.io.tunnelling import Tunnelling
from xknx.telegram.apci import DeviceDescriptorRead, IndividualAddressRead, IndividualAddressWrite, Restart,\
    APCIService,PropertyValueRead
from xknx.telegram.address import GroupAddress, GroupAddressType
#from xknx.knxip import TPDUType

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
        
    async def DeviceDescriptor_Respone_arrived(self):
        # analyse telegram
        if self.last_telegram:
            if self.last_telegram.payload:
                return self.last_telegram.payload.CODE == APCIService.DEVICE_DESCRIPTOR_RESPONSE
        return False
    
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
            TPDUType.T_Connect)
        await self.xknx.telegrams.put(telegram)
    
    async def T_Disconnect(self):
        telegram = Telegram(
            self.ia, 
            TelegramDirection.OUTGOING,
            None,
            None,
            TPDUType.T_Disconnect)
        await self.xknx.telegrams.put(telegram)

    async def T_ACK(self, seq_no):
        if seq_no == 1:
            telegram = Telegram(
                self.ia, 
                TelegramDirection.OUTGOING,
                None,
                None,
                TPDUType.T_ACK1)
        else:
            telegram = Telegram(
                self.ia, 
                TelegramDirection.OUTGOING,
                None,
                None,
                TPDUType.T_ACK)
        await self.xknx.telegrams.put(telegram)
    
    async def DeviceDescriptor_Read(self, descriptor):
        telegram = Telegram(
            self.ia, 
            TelegramDirection.OUTGOING,
            DeviceDescriptorRead(descriptor, is_numbered = True),
            prio_system = True,
            )
        await self.xknx.telegrams.put(telegram)
        
    async def PropertyValue_Read(self):
        telegram = Telegram(
            self.ia, 
            TelegramDirection.OUTGOING,
            PropertyValueRead(0,0x0b,1,1,True,1),
            prio_system = True,
            )
        await self.xknx.telegrams.put(telegram)
        
    async def IndividualAddress_Read(self):
        telegram = Telegram(
            GroupAddress(0, self.groupAddressType), 
            TelegramDirection.OUTGOING,
            IndividualAddressRead(),
            prio_system = True,
            )
        await self.xknx.telegrams.put(telegram)

    async def IndividualAddress_Write(self):
        telegram = Telegram(
            GroupAddress(0, self.groupAddressType), 
            TelegramDirection.OUTGOING,
            IndividualAddressWrite(self.ia),
            prio_system = True,
            )
        await self.xknx.telegrams.put(telegram)
        
    async def Restart(self):
        telegram = Telegram(
            self.ia, 
            TelegramDirection.OUTGOING,
            Restart(sequqence_number = 2),
            prio_system = True,
            )
        await self.xknx.telegrams.put(telegram)
        
