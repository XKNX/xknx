'''
Created on 08.12.2020

@author: mint18
'''
from xknx.telegram import Telegram, TelegramDirection, IndividualAddress,TPDUType
from xknx.io import Connect
from xknx.knxip import ConnectRequestType
from xknx.io.tunnelling import Tunnelling
from xknx.telegram.apci import DataConnected
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
        telegram1 = Telegram(
            self.ia, 
            TelegramDirection.OUTGOING,
            None,
            None,
            TPDUType.T_Connect)
        await self.xknx.telegrams.put(telegram1)

        telegram2 = Telegram(
            self.ia, 
            TelegramDirection.OUTGOING,
            DataConnected()
            )
        await self.xknx.telegrams.put(telegram2)
        
