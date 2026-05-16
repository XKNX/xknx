"""Tests for nm_individual_address_serial_number_read — KNX 03.05.02 §2.4."""

import asyncio
from unittest.mock import AsyncMock, call

from xknx import XKNX
from xknx.management.procedures.nm.nm_individual_address_serial_number_read import (
    nm_individual_address_serial_number_read,
)
from xknx.telegram import (
    GroupAddress,
    IndividualAddress,
    Telegram,
    TelegramDirection,
    apci,
)

from ....conftest import EventLoopClockAdvancer


async def test_nm_individual_address_serial_number_read(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test nm_individual_address_serial_number_read."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("1.1.5")
    serial_number = b"aabbccddeeff"

    task = asyncio.create_task(
        nm_individual_address_serial_number_read(xknx=xknx, serial=serial_number)
    )

    read_address = Telegram(
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressSerialRead(serial=serial_number),
    )
    address_reply = Telegram(
        source_address=individual_address,
        destination_address=GroupAddress("0/0/0"),
        direction=TelegramDirection.INCOMING,
        payload=apci.IndividualAddressSerialResponse(
            address=individual_address, serial=serial_number
        ),
    )

    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(read_address),
    ]
    xknx.management.process(address_reply)

    assert await task == individual_address


async def test_nm_individual_address_serial_number_read_fail(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test nm_individual_address_serial_number_read."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    serial_number = b"aabbccddeeff"

    task = asyncio.create_task(
        nm_individual_address_serial_number_read(xknx=xknx, serial=serial_number)
    )

    read_address = Telegram(
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressSerialRead(serial=serial_number),
    )

    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(read_address),
    ]
    await time_travel(3)

    assert await task is None
