"""Tests for nm_individual_address_read — KNX 03.05.02 §2.2 NM_IndividualAddress_Read."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.nm.nm_individual_address_read import (
    nm_individual_address_read,
)
from xknx.telegram import GroupAddress, IndividualAddress, Telegram, apci

from ....conftest import EventLoopClockAdvancer


async def test_nm_individual_address_read(time_travel: EventLoopClockAdvancer) -> None:
    """Test nm_individual_address_read."""
    _timeout = 2
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address_1 = IndividualAddress("1.1.4")
    individual_address_2 = IndividualAddress("15.15.255")

    task = asyncio.create_task(nm_individual_address_read(xknx=xknx, timeout=_timeout))
    address_broadcast = Telegram(
        GroupAddress("0/0/0"), payload=apci.IndividualAddressRead()
    )

    address_reply_message_1 = Telegram(
        source_address=individual_address_1,
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressResponse(),
    )

    address_reply_message_2 = Telegram(
        source_address=individual_address_2,
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressResponse(),
    )

    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(address_broadcast),
    ]
    xknx.management.process(address_reply_message_1)
    xknx.management.process(address_reply_message_2)
    await time_travel(_timeout)
    assert await task


async def test_nm_individual_address_read_multiple() -> None:
    """Test nm_individual_address_read."""
    _timeout = 2
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address_1 = IndividualAddress("1.1.4")
    individual_address_2 = IndividualAddress("15.15.255")

    task = asyncio.create_task(
        nm_individual_address_read(xknx=xknx, timeout=_timeout, raise_if_multiple=True)
    )
    address_broadcast = Telegram(
        GroupAddress("0/0/0"), payload=apci.IndividualAddressRead()
    )

    address_reply_message_1 = Telegram(
        source_address=individual_address_1,
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressResponse(),
    )

    address_reply_message_2 = Telegram(
        source_address=individual_address_2,
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressResponse(),
    )

    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(address_broadcast),
    ]
    xknx.management.process(address_reply_message_1)
    xknx.management.process(address_reply_message_2)
    # no need to wait for _timeout due to `raise_if_multiple=True``
    with pytest.raises(ManagementConnectionError):
        await task
