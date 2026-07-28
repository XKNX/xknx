"""Tests for nm_individual_address_check — KNX 03.05.02 §2.19 NM_IndividualAddress_Check."""

import asyncio
from unittest.mock import AsyncMock, call

from xknx import XKNX
from xknx.exceptions import ManagementConnectionRefused
from xknx.management.procedures.network.nm_individual_address_check import (
    nm_individual_address_check,
    nm_individual_address_check_conn,
)
from xknx.telegram import (
    IndividualAddress,
    Telegram,
    TelegramDirection,
    apci,
    tpci,
)


async def test_nm_individual_address_check_conn_success() -> None:
    """Test nm_individual_address_check_conn when device responds normally."""
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
    async with xknx.management.connection(individual_address) as conn:
        task = asyncio.create_task(nm_individual_address_check_conn(conn))
        await asyncio.sleep(0)
        assert xknx.cemi_handler.send_telegram.call_args_list == [
            call(connect),
            call(device_desc_read),
        ]
        xknx.management.process(ack)
        xknx.management.process(device_desc_resp)
        assert await task


async def test_nm_individual_address_check_conn_refused() -> None:
    """Test nm_individual_address_check_conn when device refuses the connection."""
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
    try:
        async with xknx.management.connection(individual_address) as conn:
            task = asyncio.create_task(nm_individual_address_check_conn(conn))
            await asyncio.sleep(0)
            assert xknx.cemi_handler.send_telegram.call_args_list == [
                call(connect),
                call(device_desc_read),
            ]
            xknx.management.process(disconnect)
            xknx.management.process(ack)
            assert await task
    except ManagementConnectionRefused:
        pass


async def test_nm_individual_address_check_success() -> None:
    """Test nm_individual_address_check opens and closes its own connection."""
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
    ack_out = Telegram(
        source_address=IndividualAddress(0),
        destination_address=individual_address,
        tpci=tpci.TAck(0),
    )
    device_desc_resp = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorResponse(),
    )
    disconnect = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDisconnect(),
    )

    task = asyncio.create_task(
        nm_individual_address_check(xknx.management, individual_address)
    )
    await asyncio.sleep(0)
    xknx.management.process(ack)
    xknx.management.process(device_desc_resp)

    assert await task
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
        call(ack_out),
        call(disconnect),
    ]


async def test_nm_individual_address_check_occupied_by_disconnect() -> None:
    """
    Test nm_individual_address_check when the peer disconnects during the check.

    The device sends TDisconnect before answering, so nm_individual_address_check_conn
    returns True internally; the connection context manager's own disconnect() then
    raises ManagementConnectionRefused (peer already disconnected), which is swallowed
    and the address is still reported as found/occupied.
    """
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("4.0.10")

    connect = Telegram(destination_address=individual_address, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    disconnect_from_device = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDisconnect(),
    )
    ack_from_device = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )

    task = asyncio.create_task(
        nm_individual_address_check(xknx.management, individual_address)
    )
    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
    ]
    xknx.management.process(disconnect_from_device)
    xknx.management.process(ack_from_device)

    assert await task
    assert len(xknx.cemi_handler.send_telegram.call_args_list) == 2
