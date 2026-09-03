"""Tests for dm_restart — KNX v02.01.02 - Management Procedures 03.05.02 - §3.7.3 DM_Restart_RCo."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dm_restart_r_co import (
    dm_restart,
    dm_restart_r_co,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


async def test_dm_restart_r_co() -> None:
    """Test dm_restart_r_co on an already-open connection."""
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
    async with xknx.management.connection(individual_address) as conn:
        await dm_restart_r_co(conn)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(restart),
        call(disconnect),
    ]


async def test_dm_restart() -> None:
    """Test dm_restart opens and closes its own connection."""
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
    await dm_restart(xknx, individual_address)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(restart),
        call(disconnect),
    ]


async def test_dm_restart_r_co_master_reset() -> None:
    """Test dm_restart_r_co requests a Master Reset and returns the response."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dm_restart_r_co(conn, master_reset=True, erase_code=0x01, channel_number=2)
    )
    await asyncio.sleep(0)

    expected_request = Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.RestartMasterReset(erase_code=0x01, channel_number=2),
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
        payload=apci.RestartMasterResetResponse(error_code=0, process_time=30),
    )
    xknx.management.process(ack)
    xknx.management.process(response)

    result = await task
    assert result == apci.RestartMasterResetResponse(error_code=0, process_time=30)

    await conn.disconnect()


async def test_dm_restart_r_co_master_reset_refused() -> None:
    """Test dm_restart_r_co raises when the device refuses the Master Reset."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dm_restart_r_co(conn, master_reset=True, erase_code=0x99)
    )
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
        payload=apci.RestartMasterResetResponse(error_code=0x02, process_time=0),
    )
    xknx.management.process(ack)
    xknx.management.process(response)

    with pytest.raises(ManagementConnectionError, match="Unsupported Erase Code"):
        await task

    await conn.disconnect()
