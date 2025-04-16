"""Tests for KNX/IP routing indications using multicast."""

import asyncio
from typing import Final
from unittest.mock import Mock

from xknx import XKNX
from xknx.dpt.payload import DPTBinary
from xknx.io.connection import ConnectionConfig, ConnectionType
from xknx.telegram import GroupAddress, IndividualAddress, Telegram
from xknx.telegram.apci import GroupValueWrite
from xknx.telegram.telegram import TelegramDirection
from xknx.telegram.tpci import TDataGroup
from xknx.util import asyncio_timeout

EXPERIMENTAL_MCAST_GRP: Final = "224.0.0.254"


async def test_routing_indication_multicast() -> None:
    """Test exchanging routing indication using multicast."""
    routing1_mock = Mock()
    data_received = asyncio.Event()
    received_data: Telegram | None = None

    def routing2_callback(telegram: Telegram) -> None:
        """Set test data from receiving xknx instance."""
        nonlocal received_data
        received_data = telegram
        data_received.set()

    msg = Telegram(
        destination_address=GroupAddress("1/2/2"),
        source_address=IndividualAddress("1.1.1"),
        payload=GroupValueWrite(DPTBinary(1)),
        tpci=TDataGroup(),
    )

    async with (
        XKNX(
            connection_config=ConnectionConfig(
                connection_type=ConnectionType.ROUTING,
                multicast_group=EXPERIMENTAL_MCAST_GRP,
            ),
            telegram_received_cb=routing1_mock,
        ) as xknx1,
        XKNX(
            connection_config=ConnectionConfig(
                connection_type=ConnectionType.ROUTING,
                multicast_group=EXPERIMENTAL_MCAST_GRP,
            ),
            telegram_received_cb=routing2_callback,
        ),
    ):
        await xknx1.telegrams.put(msg)
        async with asyncio_timeout(1):
            await data_received.wait()

        msg.direction = TelegramDirection.INCOMING
        routing1_mock.assert_not_called()
        assert received_data == msg
