"""Tests for nm_individual_address_serial_number_write — KNX v02.01.02 - Management Procedures 03.05.02 - §2.5."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import MANAGEMENT_CONNECTION_TIMEOUT
from xknx.management.procedures.network.nm_individual_address_serial_number_write import (
    nm_individual_address_serial_number_write,
)
from xknx.telegram import (
    GroupAddress,
    IndividualAddress,
    Telegram,
    TelegramDirection,
    apci,
    tpci,
)

from ....conftest import EventLoopClockAdvancer


def _address_check(individual_address: IndividualAddress) -> list[Telegram]:
    """Telegrams of an address check nobody answers (with the retransmit)."""
    device_desc_read = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    return [
        Telegram(destination_address=individual_address, tpci=tpci.TConnect()),
        device_desc_read,
        device_desc_read,
        Telegram(destination_address=individual_address, tpci=tpci.TDisconnect()),
    ]


async def _address_not_in_use(time_travel: EventLoopClockAdvancer) -> None:
    """Let the address check time out: no device answers at the new address."""
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)


def _address_in_use(xknx: XKNX, individual_address: IndividualAddress) -> None:
    """Answer the address check: a device responds at the new address."""
    xknx.management.process(
        Telegram(
            source_address=individual_address,
            destination_address=IndividualAddress(0),
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(0),
        )
    )
    xknx.management.process(
        Telegram(
            source_address=individual_address,
            destination_address=IndividualAddress(0),
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(0),
            payload=apci.DeviceDescriptorResponse(),
        )
    )


def _address_check_answered(individual_address: IndividualAddress) -> list[Telegram]:
    """Telegrams of an address check a device answers."""
    return [
        Telegram(destination_address=individual_address, tpci=tpci.TConnect()),
        Telegram(
            destination_address=individual_address,
            tpci=tpci.TDataConnected(0),
            payload=apci.DeviceDescriptorRead(descriptor=0),
        ),
        Telegram(
            source_address=IndividualAddress(0),
            destination_address=individual_address,
            tpci=tpci.TAck(0),
        ),
        Telegram(destination_address=individual_address, tpci=tpci.TDisconnect()),
    ]


def _serial_response(
    serial_number: bytes, individual_address: IndividualAddress
) -> Telegram:
    """Response of the device with the serial number, sent from its address."""
    return Telegram(
        source_address=individual_address,
        destination_address=GroupAddress("0/0/0"),
        direction=TelegramDirection.INCOMING,
        payload=apci.IndividualAddressSerialResponse(
            address=individual_address, serial=serial_number
        ),
    )


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
            xknx=xknx, serial=serial_number, individual_address=individual_address
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

    await _address_not_in_use(time_travel)
    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        *map(call, _address_check(individual_address)),
        call(write_address),
        call(read_address),
    ]
    xknx.management.process(_serial_response(serial_number, individual_address))
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
            xknx=xknx, serial=serial_number, individual_address=individual_address
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

    await _address_not_in_use(time_travel)
    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        *map(call, _address_check(individual_address)),
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
            xknx=xknx, serial=serial_number, individual_address=individual_address_tx
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

    await _address_not_in_use(time_travel)
    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        *map(call, _address_check(individual_address_tx)),
        call(write_address),
        call(read_address),
    ]
    xknx.management.process(_serial_response(serial_number, individual_address_rx))
    with pytest.raises(ManagementConnectionError):
        await task


async def test_nm_individual_address_serial_number_write_address_in_use(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test nothing is written when another device already uses the address."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    serial_number = b"aabbccddeeff"
    individual_address = IndividualAddress("1.1.5")

    task = asyncio.create_task(
        nm_individual_address_serial_number_write(
            xknx=xknx, serial=serial_number, individual_address=individual_address
        )
    )

    read_address = Telegram(
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressSerialRead(serial=serial_number),
    )

    await time_travel(0)
    _address_in_use(xknx, individual_address)
    await time_travel(0)
    # the device with the serial number still has another address
    xknx.management.process(
        _serial_response(serial_number, IndividualAddress("15.15.255"))
    )
    with pytest.raises(ManagementConnectionError, match="in use by another device"):
        await task

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        *map(call, _address_check_answered(individual_address)),
        call(read_address),
    ]


async def test_nm_individual_address_serial_number_write_address_in_use_no_serial(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test nothing is written when the address is in use and the serial number doesn't answer."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    serial_number = b"aabbccddeeff"
    individual_address = IndividualAddress("1.1.5")

    task = asyncio.create_task(
        nm_individual_address_serial_number_write(
            xknx=xknx, serial=serial_number, individual_address=individual_address
        )
    )

    read_address = Telegram(
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressSerialRead(serial=serial_number),
    )

    await time_travel(0)
    _address_in_use(xknx, individual_address)
    await time_travel(0)
    # no device with the serial number answers
    await time_travel(3)
    with pytest.raises(ManagementConnectionError, match="no device with serial"):
        await task

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        *map(call, _address_check_answered(individual_address)),
        call(read_address),
    ]


async def test_nm_individual_address_serial_number_write_address_in_use_by_itself(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """Test nothing is written when the device with the serial number already uses the address."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    serial_number = b"aabbccddeeff"
    individual_address = IndividualAddress("1.1.5")

    task = asyncio.create_task(
        nm_individual_address_serial_number_write(
            xknx=xknx, serial=serial_number, individual_address=individual_address
        )
    )

    read_address = Telegram(
        destination_address=GroupAddress("0/0/0"),
        payload=apci.IndividualAddressSerialRead(serial=serial_number),
    )

    await time_travel(0)
    _address_in_use(xknx, individual_address)
    await time_travel(0)
    xknx.management.process(_serial_response(serial_number, individual_address))
    await task

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        *map(call, _address_check_answered(individual_address)),
        call(read_address),
    ]
