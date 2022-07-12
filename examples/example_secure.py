"""Example for KNX IP Secure."""

import asyncio
import logging

from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.io import ConnectionConfig, ConnectionType, SecureConfig
from xknx.telegram import GroupAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueWrite

logging.basicConfig(level=logging.INFO)
logging.getLogger("xknx.log").level = logging.DEBUG
logging.getLogger("xknx.knx").level = logging.DEBUG


async def main() -> None:
    """Test connection with secure."""

    connection_config = ConnectionConfig(
        connection_type=ConnectionType.TUNNELING_TCP_SECURE,
        gateway_ip="192.168.1.188",
        secure_config=SecureConfig(
            user_id=4,
            knxkeys_file_path="/home/marvin/testcase.knxkeys",
            knxkeys_password="password",
        ),
    )
    xknx = XKNX(connection_config=connection_config)
    await xknx.start()

    await xknx.knxip_interface.send_telegram(
        Telegram(
            GroupAddress("1/0/32"),
            TelegramDirection.OUTGOING,
            GroupValueWrite(DPTBinary(1)),
        )
    )
    await asyncio.sleep(5)
    print("Tunnel connected")
    await xknx.stop()


asyncio.run(main())
