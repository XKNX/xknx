"""Example for connecting to a KNX IP Secure Tunnel."""

import asyncio
import logging

from xknx import XKNX
from xknx.io import ConnectionConfig, ConnectionType, SecureConfig
from xknx.tools import group_value_write

logging.basicConfig(level=logging.INFO)
logging.getLogger("xknx.log").level = logging.DEBUG
logging.getLogger("xknx.knx").level = logging.DEBUG


async def main() -> None:
    """Test connection with IP secure tunnelling."""

    connection_config = ConnectionConfig(
        connection_type=ConnectionType.TUNNELING_TCP_SECURE,
        gateway_ip="192.168.1.188",
        individual_address="1.0.11",
        secure_config=SecureConfig(
            knxkeys_file_path="/home/marvin/testcase.knxkeys",
            knxkeys_password="password",
        ),
    )
    xknx = XKNX(connection_config=connection_config)

    await xknx.start()
    print("Tunnel connected")
    group_value_write(xknx, "1/0/32", True)
    await asyncio.sleep(5)
    await xknx.stop()


asyncio.run(main())
