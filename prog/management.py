'''
This modul implements the management procedures as described
in KNX-Standard 3.5.2 
'''

from xknx.telegram.address import IndividualAddress, GroupAddress
from prog.device import A_Device

import asyncio
from _testcapi import awaitType
from xknx import telegram

NM_OK = 0
NM_EXISTS = 1
NM_TIME_OUT = 2

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
        if telegram.destination_address == GroupAddress("0"):
            for addr in self.reg_dev:
                await self.reg_dev[addr].process_telegram(telegram)

    async def IndividualAddress_Write(self, ia):
        
        d = A_Device(self.xknx, ia)
        self.reg_dev[ia] = d

        try:        
            await asyncio.wait_for(d.T_Connect_Response(), 0.5)
            return NM_EXISTS
        except asyncio.TimeoutError:
            pass
        
        try:
            await asyncio.wait_for(d.DeviceDescriptor_Read_Response(0), 0.5)
            await d.T_Disconnect()
            return NM_EXISTS
        except asyncio.TimeoutError:
            pass
        '''
        # wait for response
        await asyncio.sleep(0.5)
        if await d.DeviceDescriptor_Respone_arrived():
            print ("DeviceDescriptor_Respone_arrived.1")
            await d.T_Disconnect()
            return NM_EXISTS
        '''
        try:
            await asyncio.wait_for(d.IndividualAddress_Read_Response(), 600)
        except asyncio.TimeoutError:
            return NM_TIME_OUT
        '''            
        await asyncio.sleep(2)
        dst = await d.IndividualAddress_Respone()
        for i in range(240):
        #for i in range(3):
            if dst:
                break
            await d.IndividualAddress_Read()
            await asyncio.sleep(2)
            dst = await d.IndividualAddress_Respone()
            
        if not dst:
            return NM_TIME_OUT
        '''
        await d.IndividualAddress_Write()
        
        # Zusatz ETS reengeneering
        '''
        await d.IndividualAddress_Read()
        await asyncio.sleep(1)
        dst = await d.IndividualAddress_Respone()
        if dst != ia:
            print ("dst != ia:", dst, ia)
        '''
        await d.T_Connect()
        try:
            await asyncio.wait_for(d.DeviceDescriptor_Read_Response(0), 1.0)
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {self.ia}")
            
        await d.PropertyValue_Read()
        await d.Restart()
        await asyncio.sleep(1)
        await d.T_Disconnect()
        return NM_OK
        
    