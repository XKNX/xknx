"""Tests for dm_restart — KNX 03.05.02 §3.7.3 DM_Restart_RCo."""

from unittest.mock import AsyncMock, call

from xknx import XKNX
from xknx.management.procedures.device.dm_restart_r_co import (
    dm_restart,
    dm_restart_r_co,
)
from xknx.telegram import IndividualAddress, Telegram, apci, tpci


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
