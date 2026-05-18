"""Tests for nm_individual_address_check — KNX 03.05.02 §2.19 NM_IndividualAddress_Check."""

import asyncio
from unittest.mock import AsyncMock, call

from xknx import XKNX
from xknx.management.procedures.network.nm_individual_address_check import (
    nm_individual_address_check,
)
from xknx.telegram import (
    IndividualAddress,
    Telegram,
    TelegramDirection,
    apci,
    tpci,
)


async def test_nm_individual_address_check_success() -> None:
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
    task = asyncio.create_task(nm_individual_address_check(xknx, individual_address))
    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
    ]
    # receive response
    xknx.management.process(ack)
    xknx.management.process(device_desc_resp)
    assert await task


async def test_nm_individual_address_check_refused() -> None:
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
    task = asyncio.create_task(nm_individual_address_check(xknx, individual_address))
    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
    ]
    xknx.management.process(disconnect)
    xknx.management.process(ack)
    assert await task
