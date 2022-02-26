"""Example for KNX IP Secure."""

import asyncio
import logging

from xknx import XKNX
from xknx.dpt import DPTBinary
from xknx.io import ConnectionConfig, ConnectionType
from xknx.io.tunnel import SecureTunnel
from xknx.telegram import GroupAddress, Telegram, TelegramDirection
from xknx.telegram.apci import GroupValueWrite

logging.basicConfig(level=logging.INFO)
logging.getLogger("xknx.log").level = logging.DEBUG
logging.getLogger("xknx.knx").level = logging.DEBUG


async def main() -> None:
    """Test connection with secure."""

    connection_config = ConnectionConfig(
        connection_type=ConnectionType.TUNNELING,
        gateway_ip="10.1.0.40",
    )
    xknx = XKNX(connection_config=connection_config)

    tunnel = SecureTunnel(
        xknx, gateway_ip="192.168.1.100", gateway_port=3671, auto_reconnect=False
    )
    await tunnel.connect()

    await tunnel.send_telegram(
        Telegram(
            GroupAddress("1/0/32"),
            TelegramDirection.OUTGOING,
            GroupValueWrite(DPTBinary(1)),
        )
    )
    await asyncio.sleep(5)
    print("Tunnel connected")
    await tunnel.disconnect()


asyncio.run(main())
