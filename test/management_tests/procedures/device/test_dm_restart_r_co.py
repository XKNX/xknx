"""Tests for dm_restart — KNX 03.05.02 §3.7.3 DM_Restart_RCo."""

from unittest.mock import AsyncMock, call

from xknx import XKNX
from xknx.management.procedures.device.dm_restart_r_co import dm_restart
from xknx.telegram import IndividualAddress, Telegram, apci, tpci


async def test_dm_restart() -> None:
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
    async with xknx.management.connection(individual_address) as conn:
        await dm_restart(conn)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(restart),
        call(disconnect),
    ]
