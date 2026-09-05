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


async def test_dm_restart_r_co_master_reset_default_erase_code() -> None:
    """Test dm_restart_r_co defaults erase_code to 01h "Confirmed Restart"."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dm_restart_r_co(conn, master_reset=True))
    await asyncio.sleep(0)

    expected_request = Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.RestartMasterReset(erase_code=0x01, channel_number=0),
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
        payload=apci.RestartMasterResetResponse(error_code=0, process_time=5),
    )
    xknx.management.process(ack)
    xknx.management.process(response)

    result = await task
    assert result == apci.RestartMasterResetResponse(error_code=0, process_time=5)

    await conn.disconnect()


@pytest.mark.parametrize("erase_code", [0x00, 0x09, 0xFF])
async def test_dm_restart_r_co_erase_code_out_of_range(erase_code: int) -> None:
    """
    Test dm_restart_r_co rejects a reserved erase_code before sending anything.

    KNX v02.01.02 - Management Procedures 03.05.02 - §3.7.1.2.3.1, Table 4:
    only 01h-08h are defined; 00h and 09h-FFh are reserved and "the
    Management Client shall not use these Erase Codes".
    """
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    with pytest.raises(ValueError, match=r"erase_code must be 0x01-0x08"):
        await dm_restart_r_co(conn, master_reset=True, erase_code=erase_code)

    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dm_restart_r_co_master_reset_refused() -> None:
    """Test dm_restart_r_co raises when the device refuses the Master Reset."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dm_restart_r_co(conn, master_reset=True, erase_code=0x02)
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
        payload=apci.RestartMasterResetResponse(error_code=0x01, process_time=0),
    )
    xknx.management.process(ack)
    xknx.management.process(response)

    with pytest.raises(ManagementConnectionError, match="Access denied"):
        await task

    await conn.disconnect()


async def test_dm_restart_r_co_master_reset_unsupported_erase_code() -> None:
    """Test dm_restart_r_co raises with the Unsupported Erase Code reason."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dm_restart_r_co(conn, master_reset=True, erase_code=0x08)
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


async def test_dm_restart_r_co_master_reset_unknown_error_code() -> None:
    """Test dm_restart_r_co falls back to "Unknown Error" for an undocumented error code."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dm_restart_r_co(conn, master_reset=True, erase_code=0x02)
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
        payload=apci.RestartMasterResetResponse(error_code=0x7F, process_time=0),
    )
    xknx.management.process(ack)
    xknx.management.process(response)

    with pytest.raises(ManagementConnectionError, match=r"Unknown Error"):
        await task

    await conn.disconnect()


async def test_dm_restart_master_reset() -> None:
    """Test dm_restart opens and closes its own connection for a Master Reset."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    ia = IndividualAddress("4.0.10")

    task = asyncio.create_task(
        dm_restart(xknx, ia, master_reset=True, erase_code=0x02, channel_number=1)
    )
    await asyncio.sleep(0)

    connect = Telegram(destination_address=ia, tpci=tpci.TConnect())
    assert xknx.cemi_handler.send_telegram.call_args_list[0] == call(connect)

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
        payload=apci.RestartMasterResetResponse(error_code=0, process_time=5),
    )
    xknx.management.process(ack)
    xknx.management.process(response)
    await asyncio.sleep(0)

    result = await task
    assert result == apci.RestartMasterResetResponse(error_code=0, process_time=5)

    disconnect = Telegram(destination_address=ia, tpci=tpci.TDisconnect())
    assert xknx.cemi_handler.send_telegram.call_args_list[-1] == call(disconnect)
