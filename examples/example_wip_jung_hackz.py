"""Example for individual address write."""
import sys
sys.path.append('./')

import logging
import asyncio

from xknx import XKNX
from xknx.prog import ProgDevice
from xknx.prog.management import NM_EXISTS, NM_OK, NM_TIME_OUT, NetworkManagement
from xknx.telegram.address import IndividualAddress, GroupAddress
from xknx.telegram import Telegram


NM_OK = 0
NM_EXISTS = 1
NM_TIME_OUT = 2

class UltraHacker:
    """Class for network management functionality."""

    def __init__(self, xknx: XKNX):
        """Construct NM instance."""
        self.xknx = xknx
        xknx.telegram_queue.register_telegram_received_cb(self.telegram_received_cb)
        # map for registered devices
        self.reg_dev: dict[IndividualAddress, Device] = {}

    async def telegram_received_cb(self, tele: Telegram) -> None:
        """Do something with the received telegram."""
        if tele.source_address in self.reg_dev:
            await self.reg_dev[tele.source_address].process_telegram(tele)
        if tele.destination_address == GroupAddress("0"):
            for reg_dev_val in self.reg_dev.values():
                await reg_dev_val.process_telegram(tele)

    async def hack_jung_clicks(self, ind_add: IndividualAddress) -> int:
        """Perform IndividualAdress_Write."""
        device = ProgDevice(self.xknx, ind_add)
        self.reg_dev[ind_add] = device

        print("")
        print("############################")
        print("Connect")
        print("############################")
        await device.t_connect()

        print("")
        print("############################")
        print("devicedescriptor_read_response")
        print("############################")
        try:
            result = await asyncio.wait_for(device.devicedescriptor_read_response(0), 1.0)
            print(f"############### DEV DESC RESULT: {result:04x}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {ind_add}")

        print("")
        print("############################")
        print("propertyvalue_read_response")
        print("############################") 
        try:
            result = await asyncio.wait_for(device.propertyvalue_read_response(property_id=56, count=1), 1.0)
            print(f"# memory_read_response RESULT: {result}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {ind_add}")        

        print("############################")
        print("authorize_request_response")
        print("############################") 
        try:
            result = await asyncio.wait_for(device.authorize_request_response(0xFFFFFFFF), 1.0)
            print(f"# authorize_request_response RESULT: level {result}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {ind_add}")

        print("")
        print("############################")
        print("propertyvalue_read_response")
        print("############################") 
        try:
            result = await asyncio.wait_for(device.propertyvalue_read_response(property_id=11, count=1), 1.0)
            print(f"# memory_read_response RESULT: {result}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {ind_add}")        

        await asyncio.sleep(1)

        print("")
        print("############################")
        print("memory read")
        print("############################") 
        try:
            result = await asyncio.wait_for(device.memory_read_response(0xB6EC, 1), 5.0)
            print(f"# authorize_request_response RESULT: level {result}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {ind_add}")
    
        device.last_telegram = None

        print("")
        print("############################")
        print("memory read")
        print("############################") 
        try:
            result = await asyncio.wait_for(device.memory_read_response(0x453E, 1), 5.0)
            print(f"# authorize_request_response RESULT: level {result}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {ind_add}")


        print("")
        print("############################")
        print("property write")
        print("############################") 
        #274	12.347859	89	11	TunnelReq #11:27 L_Data.req 0.0.0->1.1.4 PropValueWrite OX=3 P=5 $01000000000000000000
        try:
            result = await asyncio.wait_for(device.propertyvalue_write_response(object_index=3, property_id=5, data=bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])), 5.0)
            print(f"# authorize_request_response RESULT: level {result}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {ind_add}")

        device.last_telegram = None

        print("")
        print("############################")
        print("property write")
        print("############################") 
        #298	12.678220	80	14	TunnelReq #11:33 L_Data.req 0.0.0->1.1.4 PropValueWrite OX=0 P=14 $04        try:
        try:
            result = await asyncio.wait_for(device.propertyvalue_write_response(object_index=0, property_id=14, data=bytes([0x04])), 5.0)
            print(f"# authorize_request_response RESULT: level {result}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {ind_add}")



        print("")
        print("############################")
        print("memory write")
        print("############################") 
        try:
            result = await asyncio.wait_for(device.memory_write_response(0x453E, bytes([0x12])), 5.0)
            print(f"# authorize_request_response RESULT: level {result}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {ind_add}")
               

        print("")
        print("############################")
        print("memory read")
        print("############################") 
        try:
            result = await asyncio.wait_for(device.memory_read_response(0x453E, 1), 5.0)
            print(f"# authorize_request_response RESULT: level {result}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {ind_add}")

        print("")
        print("############################")
        print("property write")
        print("############################") 
        #319	12.989015	89	1	TunnelReq #11:39 L_Data.req 0.0.0->1.1.4 PropValueWrite OX=3 P=5 $02000000000000000000

        try:
            result = await asyncio.wait_for(device.propertyvalue_write_response(object_index=3, property_id=5, data=bytes([0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])), 5.0)
            print(f"# authorize_request_response RESULT: level {result}")
        except asyncio.TimeoutError:
            raise RuntimeError(f"No device response from {ind_add}")

        await device.restart()
        await asyncio.sleep(3)
        await device.t_disconnect()
        return NM_OK


async def main():
    print("OHI")
    """Write inidividual address to device."""
    xknx = XKNX(log_directory="./logs")
    await xknx.start()

    hacker = UltraHacker(xknx)
    await hacker.hack_jung_clicks(IndividualAddress('1.1.4'))

    await xknx.stop()


logging.basicConfig(level=logging.INFO)
logging.getLogger("xknx.log").level = logging.DEBUG
#logging.getLogger("xknx.knx").level = logging.DEBUG
#logging.getLogger("xknx.raw_socket").level = logging.DEBUG
print("hi")
#asyncio.run(main())
