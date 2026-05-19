"""Tests for dm_connect — KNX 03.05.02 §3.2.1 DMP_Connect_RCo."""

import asyncio
from unittest.mock import AsyncMock, call

from xknx import XKNX
from xknx.management.procedures.device.dm_connect import dm_connect
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


async def test_dm_connect_reads_device_descriptor() -> None:
    """Test dm_connect sends DeviceDescriptorRead(0) and returns the DD0 value."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dm_connect(conn))
    await asyncio.sleep(0)

    expected_request = Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    assert xknx.cemi_handler.send_telegram.call_args_list == [call(expected_request)]

    ack = Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    response = Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorResponse(descriptor=0, value=0x07B0),
    )
    xknx.management.process(ack)
    xknx.management.process(response)

    mask_version = await task
    assert mask_version == 0x07B0

    await conn.disconnect()
