"""Test management handling."""
import asyncio
from unittest.mock import call, patch

import pytest

from xknx import XKNX
from xknx.exceptions import (
    CommunicationError,
    ConfirmationError,
    ManagementConnectionError,
    ManagementConnectionTimeout,
)
from xknx.management.management import MANAGAMENT_ACK_TIMEOUT
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


@patch("xknx.io.knxip_interface.KNXIPInterface", autospec=True)
async def test_connect(_if_mock):
    """Test establishing connections."""
    xknx = XKNX()
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

    await xknx.management.connect(ia_1)
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


@patch("xknx.io.knxip_interface.KNXIPInterface", autospec=True)
async def test_ack_timeout(_if_mock, time_travel):
    """Test ACK timeout handling."""
    xknx = XKNX()
    _ia = IndividualAddress("4.0.1")

    conn = await xknx.management.connect(_ia)
    xknx.knxip_interface.send_telegram.reset_mock()

    device_desc_read = Telegram(
        destination_address=_ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    task = asyncio.create_task(
        conn.request(
            payload=apci.DeviceDescriptorRead(descriptor=0),
            expected=apci.DeviceDescriptorResponse,
        )
    )
    await asyncio.sleep(0)
    assert xknx.knxip_interface.send_telegram.call_args_list == [
        call(device_desc_read),
    ]
    await time_travel(MANAGAMENT_ACK_TIMEOUT)
    # telegram repeated
    assert xknx.knxip_interface.send_telegram.call_args_list == [
        call(device_desc_read),
        call(device_desc_read),
    ]
    await time_travel(MANAGAMENT_ACK_TIMEOUT)
    with pytest.raises(ManagementConnectionTimeout):
        # still no ACK -> timeout
        await task

    await conn.disconnect()


@patch("xknx.io.knxip_interface.KNXIPInterface", autospec=True)
async def test_failed_connect_disconnect(_if_mock):
    """Test failing connections."""
    xknx = XKNX()
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


async def test_reject_incoming_connection():
    """Test rejecting incoming transport connections."""
    # Note: incoming L_DATA.ind indication connection requests are rejected
    # L_DATA.req frames received from a tunnelling client are not yet supported
    xknx = XKNX()
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
    with patch("xknx.io.KNXIPInterface.send_telegram") as send_telegram:
        xknx.knxip_interface.telegram_received(connect)
        await asyncio.sleep(0)
        assert send_telegram.call_args_list == [call(disconnect)]


async def test_incoming_unexpected_numbered_telegram():
    """Test incoming unexpected numbered telegram is acked."""
    xknx = XKNX()
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
    with patch("xknx.io.KNXIPInterface.send_telegram") as send_telegram:
        xknx.knxip_interface.telegram_received(device_desc_read)
        await asyncio.sleep(0)
        assert send_telegram.call_args_list == [call(ack)]


async def test_incoming_wrong_address():
    """Test incoming telegrams addressed to different devices."""
    xknx = XKNX()
    individual_address = IndividualAddress("4.0.10")
    other_address = IndividualAddress("4.0.11")
    assert xknx.current_address != other_address

    connect = Telegram(
        source_address=individual_address,
        destination_address=other_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TConnect(),
    )
    ack = Telegram(
        source_address=individual_address,
        destination_address=other_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    disconnect = Telegram(
        source_address=individual_address,
        destination_address=other_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDisconnect(),
    )
    with patch("xknx.io.KNXIPInterface.send_telegram") as send_telegram:
        xknx.knxip_interface.telegram_received(connect)
        xknx.knxip_interface.telegram_received(ack)
        xknx.knxip_interface.telegram_received(disconnect)
        await asyncio.sleep(0)
        send_telegram.assert_not_called()
