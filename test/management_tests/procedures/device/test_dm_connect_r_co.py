"""Tests for dmp_connect_r_co — KNX v02.01.02 - Management Procedures 03.05.02 - §3.2.1 DMP_Connect_RCo."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dm_connect_r_co import dmp_connect_r_co
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


async def test_dmp_connect_r_co_reads_device_descriptor() -> None:
    """Test dmp_connect_r_co sends DeviceDescriptorRead(0) and returns the DD0 value."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dmp_connect_r_co(conn))
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


async def test_dmp_connect_r_co_rejects_unexpected_descriptor_type() -> None:
    """Test dmp_connect_r_co raises if the response isn't Device Descriptor Type 0."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dmp_connect_r_co(conn))
    await asyncio.sleep(0)

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
        payload=apci.DeviceDescriptorResponse(descriptor=2, value=0x1234),
    )
    xknx.management.process(ack)
    xknx.management.process(response)

    with pytest.raises(ManagementConnectionError):
        await task

    await conn.disconnect()
