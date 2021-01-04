'''
Created on 08.12.2020

@author: mint18
'''
from xknx.telegram.address import IndividualAddress
from xknx.telegram import Telegram

import asyncio
from xknx.telegram.apci import Connect, GroupValueRead
from xknx.telegram.telegram import TelegramDirection

class Device:
    '''
    defines a device as programming unit
    '''
    def __init__(self, xknx, ia:IndividualAddress):
        self.xknx = xknx
        self.ia = ia
    
    async def check_existence(self):
        telegram = Telegram(self.ia, TelegramDirection.OUTGOING, Connect())
        
        #await asyncio.wait(self.xknx.telegrams.put(telegram), 1.0)
        await self.xknx.telegrams.put(telegram)
        
