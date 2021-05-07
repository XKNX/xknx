'''
This modul implements the management procedures as described
in KNX-Standard 3.5.2 
'''

from xknx.telegram.address import IndividualAddress
from prog.device import A_Device

import asyncio
from _testcapi import awaitType

NM_OK = 0
NM_EXISTS = 1

class NetworkManagement:
    
    def __init__(self, xknx):
        self.xknx = xknx
        xknx.telegram_queue.register_telegram_received_cb(
            self.telegram_received_cb
            )
        # map for registered devices
        self.reg_dev = {}

    async def telegram_received_cb(self, telegram):
        """Do something with the received telegram."""
        print(f"Telegram received: {telegram}")
        if telegram.source_address in self.reg_dev:
            await self.reg_dev[telegram.source_address].process_telegram(telegram)
    

    async def IndividualAddress_Write(self, ia):
        
        d = A_Device(self.xknx, ia)
        
        self.reg_dev[ia] = d
        await d.T_Connect()
        await d.DeviceDescriptor_Read(0)
        # wait for response
        await asyncio.sleep(0.5)
        if await d.DeviceDescriptor_Respone_arrived():
            print ("DeviceDescriptor_Respone_arrived")
            await d.T_Disconnect()
            return NM_EXISTS
        
        
        await d.IndividualAddress_Read()
        await d.IndividualAddress_Write()
        await d.connect()
        await d.DeviceDescriptor_Read(0)
        await d.Restart()
        
        return NM_OK
    