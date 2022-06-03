"""Test management handling."""
import asyncio
from unittest.mock import patch

from xknx import XKNX
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, tpci


@patch("xknx.io.knxip_interface.KNXIPInterface", autospec=True)
async def test_reject_incoming_connection(_if_mock):
    """Test rejecting incoming transport connections."""
    xknx = XKNX()
    await xknx.management.start()
    individual_address = IndividualAddress("4.0.10")

    connect = Telegram(
        source_address=individual_address,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TConnect(),
    )
    disconnect = Telegram(
        source_address=xknx.current_address,
        destination_address=individual_address,
        tpci=tpci.TDisconnect(),
    )

    xknx.management.incoming_queue.put_nowait(connect)
    await asyncio.sleep(0)
    xknx.knxip_interface.send_telegram.assert_called_once_with(disconnect)
    await xknx.management.stop()
