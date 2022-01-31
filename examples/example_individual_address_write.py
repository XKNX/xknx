"""Example for individual address write."""
import asyncio

from xknx import XKNX
from xknx.prog.management import NM_EXISTS, NM_OK, NM_TIME_OUT, NetworkManagement
from xknx.telegram.address import IndividualAddress

# import logging


async def main():
    """Write inidividual address to device."""
    # xknx = XKNX(log_directory="/home/sparky2021/tmp")
    xknx = XKNX()
    await xknx.start()
    network_management = NetworkManagement(xknx)
    return_code = await network_management.individualaddress_write(
        IndividualAddress("1.2.1")
    )
    if return_code == NM_OK:
        print("Individual address write succeeded.")
    elif return_code == NM_EXISTS:
        print("Individual address already occupied.")
    elif return_code == NM_TIME_OUT:
        print("Individual address write reached time out.")
    else:
        raise RuntimeError("IndividualAddress_Write retuned unknown return code")
    await asyncio.sleep(5)
    await xknx.stop()


# logging.basicConfig(level=logging.INFO)
# logging.getLogger("xknx.log").level = logging.DEBUG
# logging.getLogger("xknx.knx").level = logging.DEBUG
# logging.getLogger("xknx.raw_socket").level = logging.DEBUG

asyncio.run(main())
