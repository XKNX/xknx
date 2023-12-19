"""Test management procedures."""
import asyncio
from unittest.mock import AsyncMock, call

from xknx import XKNX
from xknx.management import procedures
from xknx.telegram import (
    GroupAddress,
    IndividualAddress,
    Telegram,
    TelegramDirection,
    apci,
    tpci,
)


async def test_dm_restart():
    """Test dm_restart."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("4.0.10")

    connect = Telegram(destination_address=individual_address, tpci=tpci.TConnect())
    restart = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDataConnected(0),
        payload=apci.Restart(),
    )
    disconnect = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDisconnect(),
    )
    await procedures.dm_restart(xknx, individual_address)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(restart),
        call(disconnect),
    ]


async def test_nm_individual_address_check_success():
    """Test nm_individual_address_check."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("4.0.10")

    connect = Telegram(destination_address=individual_address, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    ack = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    device_desc_resp = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorResponse(),
    )
    task = asyncio.create_task(
        procedures.nm_individual_address_check(xknx, individual_address)
    )
    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
    ]
    # receive response
    xknx.management.process(ack)
    xknx.management.process(device_desc_resp)
    assert await task


async def test_nm_individual_address_check_refused():
    """Test nm_individual_address_check."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("4.0.10")

    connect = Telegram(destination_address=individual_address, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    ack = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    disconnect = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDisconnect(),
    )
    task = asyncio.create_task(
        procedures.nm_individual_address_check(xknx, individual_address)
    )
    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
    ]
    xknx.management.process(disconnect)
    xknx.management.process(ack)
    assert await task


async def test_nm_individual_address_read():
    """Test nm_individual_address_read."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address_1 = IndividualAddress("1.1.4")
    individual_address_2 = IndividualAddress("15.15.255")

    task = asyncio.create_task(
        procedures.nm_individual_address_read(xknx=xknx, timeout=0.01)
    )
    address_broadcast = Telegram(
        GroupAddress("0/0/0"), payload=apci.IndividualAddressRead()
    )

    address_reply_message_1 = Telegram(
        source_address=individual_address_1,
        destination_address=GroupAddress("0/0/0"),
        direction=TelegramDirection.OUTGOING,
        payload=apci.IndividualAddressResponse(),
    )

    address_reply_message_2 = Telegram(
        source_address=individual_address_2,
        destination_address=GroupAddress("0/0/0"),
        direction=TelegramDirection.OUTGOING,
        payload=apci.IndividualAddressResponse(),
    )

    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(address_broadcast),
    ]
    xknx.management.process(address_reply_message_1)
    xknx.management.process(address_reply_message_2)
    assert await task
