"""Test management handling."""
import asyncio
from unittest.mock import call, patch

import pytest

from xknx import XKNX
from xknx.exceptions import (
    CommunicationError,
    ConfirmationError,
    ManagementConnectionError,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


@patch("xknx.io.knxip_interface.KNXIPInterface", autospec=True)
async def test_connect(_if_mock):
    """Test establishing connections."""
    xknx = XKNX()
    await xknx.management.start()
    ia_1 = IndividualAddress("4.0.1")
    ia_2 = IndividualAddress("4.0.2")

    def tg_connect(ia):
        return Telegram(
            source_address=xknx.current_address,
            destination_address=ia,
            direction=TelegramDirection.OUTGOING,
            tpci=tpci.TConnect(),
        )

    def tg_disconnect(ia):
        return Telegram(
            source_address=xknx.current_address,
            destination_address=ia,
            direction=TelegramDirection.OUTGOING,
            tpci=tpci.TDisconnect(),
        )

    conn_1 = await xknx.management.connect(ia_1)
    conn_2 = await xknx.management.connect(ia_2)

    with pytest.raises(ManagementConnectionError):
        # no 2 connections to the same IA
        await xknx.management.connect(ia_1)

    assert xknx.knxip_interface.send_telegram.call_args_list == [
        call(tg_connect(ia_1)),
        call(tg_connect(ia_2)),
    ]
    xknx.knxip_interface.send_telegram.reset_mock()

    await xknx.management.disconnect(ia_1)
    await conn_2.disconnect()

    assert xknx.knxip_interface.send_telegram.call_args_list == [
        call(tg_disconnect(ia_1)),
        call(tg_disconnect(ia_2)),
    ]

    # connect again doesn't raise
    await xknx.management.connect(ia_1)

    await xknx.management.stop()


@patch("xknx.io.knxip_interface.KNXIPInterface", autospec=True)
async def test_failed_connect_disconnect(_if_mock):
    """Test failing connections."""
    xknx = XKNX()
    await xknx.management.start()
    ia_1 = IndividualAddress("4.0.1")

    xknx.knxip_interface.send_telegram.side_effect = ConfirmationError("")
    with pytest.raises(ManagementConnectionError):
        await xknx.management.connect(ia_1)

    xknx.knxip_interface.send_telegram.side_effect = CommunicationError("")
    with pytest.raises(ManagementConnectionError):
        await xknx.management.connect(ia_1)

    xknx.knxip_interface.send_telegram.side_effect = None
    conn_1 = await xknx.management.connect(ia_1)
    xknx.knxip_interface.send_telegram.side_effect = ConfirmationError("")
    with pytest.raises(ManagementConnectionError):
        await xknx.management.disconnect(ia_1)

    xknx.knxip_interface.send_telegram.side_effect = None
    conn_1 = await xknx.management.connect(ia_1)
    xknx.knxip_interface.send_telegram.side_effect = CommunicationError("")
    with pytest.raises(ManagementConnectionError):
        await conn_1.disconnect()

    await xknx.management.stop()


@patch("xknx.io.knxip_interface.KNXIPInterface", autospec=True)
async def test_reject_incoming_connection(_if_mock):
    """Test rejecting incoming transport connections."""
    # Note: incoming L_DATA.ind indication connection requests are rejected
    # L_DATA.req frames received from a tunnelling server are not yet supported
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


@patch("xknx.io.knxip_interface.KNXIPInterface", autospec=True)
async def test_incoming_unexpected_numbered_telegram(_if_mock):
    """Test incoming unexpected numbered telegram is acked."""
    xknx = XKNX()
    await xknx.management.start()
    individual_address = IndividualAddress("4.0.10")

    device_desc_read = Telegram(
        source_address=individual_address,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    ack = Telegram(
        source_address=xknx.current_address,
        destination_address=individual_address,
        direction=TelegramDirection.OUTGOING,
        tpci=tpci.TAck(0),
    )
    xknx.management.incoming_queue.put_nowait(device_desc_read)
    await asyncio.sleep(0)
    xknx.knxip_interface.send_telegram.assert_called_once_with(ack)
    await xknx.management.stop()
