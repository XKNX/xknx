from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType
import asyncio
from xknx.tools import group_value_write
from xknx.management import procedures
from xknx.telegram import IndividualAddress, apci, Telegram, GroupAddress
from xknx.telegram.address import IndividualAddressableType
from xknx.exceptions import ManagementConnectionRefused, ManagementConnectionTimeout
import logging
from xknx.util import asyncio_timeout

logger = logging.getLogger("xknx.management.procedures")

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("xknx.log").level = logging.DEBUG
logging.getLogger("xknx.knx").level = logging.DEBUG

timeout_in_seconds = 5

async def main2():
    async with XKNX(
            log_directory="log/",
            connection_config=ConnectionConfig(
                connection_type=ConnectionType.TUNNELING,
                gateway_ip="172.149.20.28",
                gateway_port=3671,
            ),

    ) as xknx:
        individual_address = IndividualAddress("1.1.20")
        task = asyncio.create_task(
            procedures.dm_mem_read(xknx, individual_address, 0x4000, 0x4100)
        )

        result = await task
        print(result)



if __name__ == "__main__":
    asyncio.run(main2())
