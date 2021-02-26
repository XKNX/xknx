'''
Created on 08.12.2020

@author: mint18
'''
from xknx.telegram import Telegram, TelegramDirection, IndividualAddress,TPDUType
from xknx.io import Connect
from xknx.knxip import ConnectRequestType
#from xknx.knxip import TPDUType

class Device:
    '''
    defines a device as programming unit
    '''
    def __init__(self, xknx, ia:IndividualAddress):
#    def __init__(self, xknx, ia):
        self.xknx = xknx
        self.ia = ia
    
    async def check_existence(self):
        
        
        # get UDP client
        udp_client = self.xknx.knxip_interface.interface.udp_client
        connect = Connect(
            self.xknx, 
            udp_client,
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
        #await asyncio.wait(self.xknx.telegrams.put(telegram), 1.0)
        await self.xknx.telegrams.put(telegram)
        '''
