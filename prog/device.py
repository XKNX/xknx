'''
This module implements the application layer functionality of a device.
'''
from enum import Enum

from xknx.telegram import Telegram, TelegramDirection, IndividualAddress,TPDUType
#from xknx.io import Connect
#from xknx.knxip import ConnectRequestType
#from xknx.io.tunnelling import Tunnelling
from xknx.telegram.apci import DeviceDescriptorRead, IndividualAddressRead, IndividualAddressWrite, Restart
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
#    def __init__(self, xknx, ia):
        self.xknx = xknx
        self.ia = ia
        #self.state = ConnectionState.NOT_CONNECTED
        self.groupAddressType = groupAddressType
    
    async def connect(self):
        
        '''        
        # get UDP client
        udp_client = self.xknx.knxip_interface.interface.udp_client
        connect = Connect(
            self.xknx, 
            udp_client,
            False,
            ConnectRequestType.DEVICE_MGMT_CONNECTION,
            self.ia)
        await connect.start()
        if connect.success:
            print ("successssssssssssss")
        
        '''
        #telegram = Telegram(self.ia, TelegramDirection.OUTGOING, Connect())
        telegram = Telegram(
            self.ia, 
            TelegramDirection.OUTGOING,
            None,
            None,
            TPDUType.T_Connect)
        await self.xknx.telegrams.put(telegram)
    
    async def DeviceDescriptor_Read(self, descriptor):
        telegram = Telegram(
            self.ia, 
            TelegramDirection.OUTGOING,
            DeviceDescriptorRead(descriptor, is_numbered = True),
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
            Restart(),
            prio_system = True,
            )
        await self.xknx.telegrams.put(telegram)
        
