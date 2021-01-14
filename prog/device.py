'''
Created on 08.12.2020

@author: mint18
'''
from xknx.telegram.address import IndividualAddress
from xknx.telegram import Telegram

import asyncio
from xknx.telegram.apci import Connect, GroupValueRead
from xknx.telegram.telegram import TelegramDirection
from xknx.knxip.tpdu import TPDU, TPDUTelegram
from xknx.knxip.knxip_enum import TPDUType

class Device:
    '''
    defines a device as programming unit
    '''
    def __init__(self, xknx, ia:IndividualAddress):
        self.xknx = xknx
        self.ia = ia
    
    async def check_existence(self):
        #telegram = Telegram(self.ia, TelegramDirection.OUTGOING, Connect())
        telegram = TPDUTelegram(self.ia, TelegramDirection.OUTGOING, TPDUType.T_Connect)
        #await asyncio.wait(self.xknx.telegrams.put(telegram), 1.0)
        await self.xknx.telegrams.put(telegram)
        
