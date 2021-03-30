'''
This modul implements the management procedures as describes
in KNX-Standard 3.5.2 
'''

from xknx.telegram.address import IndividualAddress
from prog.device import A_Device

import asyncio

class NetworkManagement:
    
    def __init__(self, xknx):
        self.xknx = xknx

    async def IndividualAddress_Write(self, ia):
        
        d = A_Device(self.xknx, ia)    
        await d.connect()
        await d.DeviceDescriptor_Read(0)
        await d.IndividualAddress_Read()
        await d.IndividualAddress_Write()
        await d.connect()
        await d.DeviceDescriptor_Read(0)
        await d.Restart()
        await asyncio.sleep(5)
