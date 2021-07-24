'''
Created on 24.07.2021

@author: bonzius
'''
import asyncio
# import logging


from xknx.telegram.address import IndividualAddress
from xknx import XKNX
from prog.management import NetworkManagement, NM_OK, NM_EXISTS, NM_TIME_OUT 

async def main():
    """Connect to KNX/IP device, switch on outlet, wait 2 seconds and switch of off again."""
    xknx = XKNX(log_directory="/home/antix19/tmp")
    await xknx.start()
    nm = NetworkManagement(xknx)
    rc = await nm.IndividualAddress_Write(IndividualAddress("1.2.1"))
    if rc == NM_OK:
        print ("Individual address write succeeded.")
    elif rc == NM_EXISTS:
        print ("Individual address already occupied.")
    elif rc == NM_TIME_OUT:
        print ("Individual address write reached time out.")
    else:
        raise RuntimeError("IndividualAddress_Write retuned unknown return code")
    await asyncio.sleep(5)
    await xknx.stop()
    


# logging.basicConfig(level=logging.INFO)
# logging.getLogger("xknx.log").level = logging.DEBUG
# logging.getLogger("xknx.knx").level = logging.DEBUG
# logging.getLogger("xknx.raw_socket").level = logging.DEBUG

asyncio.run(main())

