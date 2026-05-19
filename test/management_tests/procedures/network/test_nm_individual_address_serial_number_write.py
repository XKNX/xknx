"""Tests for nm_individual_address_serial_number_write — KNX 03.05.02 §2.5."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.network.nm_individual_address_serial_number_write import (
    nm_individual_address_serial_number_write,
)
from xknx.telegram import (
    GroupAddress,
    IndividualAddress,
    Telegram,
    TelegramDirection,
    apci,
)

from ....conftest import EventLoopClockAdvancer


async def test_nm_individual_address_serial_number_write(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test nm_individual_address_serial_number_write."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    serial_number = b"aabbccddeeff"
    individual_address = IndividualAddress("1.1.5")

    task = asyncio.create_task(
        nm_individual_address_serial_number_write(
            xknx.management, serial=serial_number, individual_address=individual_address
        )
    )

    write_address = Telegram(
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressSerialWrite(
            serial=serial_number, address=individual_address
        ),
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
        call(write_address),
        call(read_address),
    ]
    xknx.management.process(address_reply)
    await task


async def test_nm_individual_address_serial_number_write_fail_no_response(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test nm_individual_address_serial_number_write."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    serial_number = b"aabbccddeeff"
    individual_address = IndividualAddress("1.1.5")

    task = asyncio.create_task(
        nm_individual_address_serial_number_write(
            xknx.management, serial=serial_number, individual_address=individual_address
        )
    )

    write_address = Telegram(
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressSerialWrite(
            serial=serial_number, address=individual_address
        ),
    )
    read_address = Telegram(
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressSerialRead(serial=serial_number),
    )

    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(write_address),
        call(read_address),
    ]
    await time_travel(3)
    with pytest.raises(ManagementConnectionError):
        await task


async def test_nm_individual_address_serial_number_write_fail_wrong_address(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test nm_individual_address_serial_number_write."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    serial_number = b"aabbccddeeff"
    individual_address_tx = IndividualAddress("1.1.5")
    individual_address_rx = IndividualAddress("1.1.6")

    task = asyncio.create_task(
        nm_individual_address_serial_number_write(
            xknx.management,
            serial=serial_number,
            individual_address=individual_address_tx,
        )
    )

    write_address = Telegram(
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressSerialWrite(
            serial=serial_number, address=individual_address_tx
        ),
    )
    read_address = Telegram(
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressSerialRead(serial=serial_number),
    )
    address_reply = Telegram(
        source_address=individual_address_rx,
        destination_address=GroupAddress("0/0/0"),
        direction=TelegramDirection.INCOMING,
        payload=apci.IndividualAddressSerialResponse(
            address=individual_address_rx, serial=serial_number
        ),
    )

    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(write_address),
        call(read_address),
    ]
    xknx.management.process(address_reply)
    with pytest.raises(ManagementConnectionError):
        await task
