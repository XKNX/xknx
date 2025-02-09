"""Test management procedures."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management import procedures
from xknx.management.management import MANAGAMENT_CONNECTION_TIMEOUT
from xknx.telegram import (
    GroupAddress,
    IndividualAddress,
    Telegram,
    TelegramDirection,
    apci,
    tpci,
)


async def test_dm_restart():
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
    await procedures.dm_restart(xknx, individual_address)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(restart),
        call(disconnect),
    ]


async def test_nm_individual_address_check_success():
    """Test nm_individual_address_check."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("4.0.10")

    connect = Telegram(destination_address=individual_address, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    ack = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    device_desc_resp = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorResponse(),
    )
    task = asyncio.create_task(
        procedures.nm_individual_address_check(xknx, individual_address)
    )
    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
    ]
    # receive response
    xknx.management.process(ack)
    xknx.management.process(device_desc_resp)
    assert await task


async def test_nm_individual_address_check_refused():
    """Test nm_individual_address_check."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("4.0.10")

    connect = Telegram(destination_address=individual_address, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    ack = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    disconnect = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDisconnect(),
    )
    task = asyncio.create_task(
        procedures.nm_individual_address_check(xknx, individual_address)
    )
    await asyncio.sleep(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
    ]
    xknx.management.process(disconnect)
    xknx.management.process(ack)
    assert await task


async def test_nm_individual_address_read(time_travel):
    """Test nm_individual_address_read."""
    _timeout = 2
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address_1 = IndividualAddress("1.1.4")
    individual_address_2 = IndividualAddress("15.15.255")

    task = asyncio.create_task(
        procedures.nm_individual_address_read(xknx=xknx, timeout=_timeout)
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
    await time_travel(_timeout)
    assert await task


async def test_nm_individual_address_read_multiple():
    """Test nm_individual_address_read."""
    _timeout = 2
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address_1 = IndividualAddress("1.1.4")
    individual_address_2 = IndividualAddress("15.15.255")

    task = asyncio.create_task(
        procedures.nm_individual_address_read(
            xknx=xknx, timeout=_timeout, raise_if_multiple=True
        )
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


async def test_nm_individual_address_write(time_travel):
    """Test nm_individual_address_write."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address_old = IndividualAddress("15.15.255")
    individual_address_new = IndividualAddress("1.1.4")

    connect = Telegram(destination_address=individual_address_new, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address_new,
        tpci=tpci.TDataConnected(0),
        direction=TelegramDirection.OUTGOING,
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )

    address_reply_message = Telegram(
        source_address=individual_address_old,
        destination_address=GroupAddress("0/0/0"),
        direction=TelegramDirection.INCOMING,
        payload=apci.IndividualAddressResponse(),
    )

    device_desc_resp = Telegram(
        source_address=individual_address_new,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorResponse(),
    )
    ack = Telegram(
        source_address=individual_address_new,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    ack2 = Telegram(
        destination_address=individual_address_new,
        source_address=IndividualAddress(0),
        direction=TelegramDirection.OUTGOING,
        tpci=tpci.TAck(0),
    )
    disconnect = Telegram(
        destination_address=individual_address_new,
        tpci=tpci.TDisconnect(),
    )
    individual_address_read = Telegram(
        GroupAddress("0/0/0"), payload=apci.IndividualAddressRead()
    )
    individual_address_write = Telegram(
        GroupAddress("0/0/0"),
        payload=apci.IndividualAddressWrite(address=individual_address_new),
    )
    task = asyncio.create_task(
        procedures.nm_individual_address_write(
            xknx=xknx, individual_address=individual_address_new
        )
    )

    # make sure first request (address check) times out
    await time_travel(MANAGAMENT_CONNECTION_TIMEOUT)
    await time_travel(MANAGAMENT_CONNECTION_TIMEOUT)

    # send response to device in programming mode
    xknx.management.process(address_reply_message)

    # confirm device is up and running
    await time_travel(MANAGAMENT_CONNECTION_TIMEOUT)
    xknx.management.process(ack)
    xknx.management.process(device_desc_resp)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
        call(device_desc_read),  # due to retransmit
        call(disconnect),
        call(individual_address_read),
        call(individual_address_write),
        call(connect),
        call(device_desc_read),
        call(ack2),
    ]

    await task


async def test_nm_individual_address_write_two_devices_in_programming_mode(time_travel):
    """Test nm_individual_address_write."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address_old = IndividualAddress("15.15.255")
    individual_address_new = IndividualAddress("1.1.4")

    connect = Telegram(destination_address=individual_address_new, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address_new,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    address_reply_message = Telegram(
        source_address=individual_address_old,
        destination_address=GroupAddress("0/0/0"),
        direction=TelegramDirection.INCOMING,
        payload=apci.IndividualAddressResponse(),
    )
    disconnect = Telegram(
        destination_address=individual_address_new,
        tpci=tpci.TDisconnect(),
    )
    individual_address_read = Telegram(
        GroupAddress("0/0/0"), payload=apci.IndividualAddressRead()
    )

    task = asyncio.create_task(
        procedures.nm_individual_address_write(
            xknx=xknx, individual_address=individual_address_new
        )
    )

    # make sure first request (address check) times out
    await time_travel(0)  # start
    await time_travel(3)  # first timeout
    await time_travel(3)  # second timeout

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
        call(device_desc_read),  # due to retransmit
        call(disconnect),
        call(individual_address_read),
    ]
    # receive two responses from devices in programming mode
    xknx.management.process(address_reply_message)
    xknx.management.process(address_reply_message)
    with pytest.raises(
        ManagementConnectionError,
        match="More than one KNX device is in programming mode",
    ):
        await task
    assert len(xknx.cemi_handler.send_telegram.call_args_list) == 5


async def test_nm_individual_address_write_no_device_programming_mode(time_travel):
    """Test nm_individual_address_write."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address_new = IndividualAddress("1.1.4")

    connect = Telegram(destination_address=individual_address_new, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address_new,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    disconnect = Telegram(
        destination_address=individual_address_new,
        tpci=tpci.TDisconnect(),
    )
    individual_address_read = Telegram(
        GroupAddress("0/0/0"), payload=apci.IndividualAddressRead()
    )

    task = asyncio.create_task(
        procedures.nm_individual_address_write(
            xknx=xknx, individual_address=individual_address_new
        )
    )

    # make sure first request (address check) times out
    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
    ]
    # first timeout - retransmit DeviceDescriptorRead
    await time_travel(3)
    assert xknx.cemi_handler.send_telegram.call_args_list[2:] == [
        call(device_desc_read),
    ]
    # retry also timed out
    await time_travel(3)
    assert xknx.cemi_handler.send_telegram.call_args_list[3:] == [
        call(disconnect),
        call(individual_address_read),
    ]
    # IndividualAddressRead also times out
    await time_travel(3)
    with pytest.raises(
        ManagementConnectionError, match="No device in programming mode"
    ):
        await task
    assert len(xknx.cemi_handler.send_telegram.call_args_list) == 5


async def test_nm_individual_address_write_address_found(time_travel):
    """Test nm_individual_address_write."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("1.1.4")

    connect = Telegram(destination_address=individual_address, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    ack_in = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    ack_out = Telegram(
        source_address=IndividualAddress(0),
        destination_address=individual_address,
        tpci=tpci.TAck(0),
    )
    device_desc_resp = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorResponse(),
    )
    disconnect = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDisconnect(),
    )
    individual_address_read = Telegram(
        GroupAddress("0/0/0"), payload=apci.IndividualAddressRead()
    )

    task = asyncio.create_task(
        procedures.nm_individual_address_write(
            xknx=xknx, individual_address=individual_address
        )
    )

    # first request (address check) succeeds
    await time_travel(0)
    xknx.management.process(ack_in)
    xknx.management.process(device_desc_resp)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
        call(ack_out),
    ]
    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list[3:] == [
        call(disconnect),
        call(individual_address_read),
    ]
    # second request times out - no device in programming mode
    await time_travel(3)
    with pytest.raises(
        ManagementConnectionError, match="No device in programming mode"
    ):
        await task
    assert len(xknx.cemi_handler.send_telegram.call_args_list) == 5


async def test_nm_individual_address_write_programming_failed(time_travel):
    """Test nm_individual_address_write."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address_old = IndividualAddress("15.15.255")
    individual_address_new = IndividualAddress("1.1.4")

    connect = Telegram(destination_address=individual_address_new, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address_new,
        tpci=tpci.TDataConnected(0),
        direction=TelegramDirection.OUTGOING,
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )

    address_reply_message = Telegram(
        source_address=individual_address_old,
        destination_address=GroupAddress("0/0/0"),
        direction=TelegramDirection.INCOMING,
        payload=apci.IndividualAddressResponse(),
    )
    disconnect = Telegram(
        destination_address=individual_address_new,
        tpci=tpci.TDisconnect(),
    )
    individual_address_read = Telegram(
        GroupAddress("0/0/0"), payload=apci.IndividualAddressRead()
    )
    individual_address_write = Telegram(
        GroupAddress("0/0/0"),
        payload=apci.IndividualAddressWrite(address=individual_address_new),
    )
    task = asyncio.create_task(
        procedures.nm_individual_address_write(
            xknx=xknx, individual_address=individual_address_new
        )
    )

    # make sure first request (address check) times out
    await time_travel(MANAGAMENT_CONNECTION_TIMEOUT)
    await time_travel(MANAGAMENT_CONNECTION_TIMEOUT)

    # send response to device in programming mode
    xknx.management.process(address_reply_message)

    # device experienced error, so set connection request timeout
    await time_travel(MANAGAMENT_CONNECTION_TIMEOUT)
    await time_travel(MANAGAMENT_CONNECTION_TIMEOUT)
    await time_travel(MANAGAMENT_CONNECTION_TIMEOUT)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
        call(device_desc_read),  # due to retransmit
        call(disconnect),
        call(individual_address_read),
        call(individual_address_write),
        call(connect),
        call(device_desc_read),
        call(device_desc_read),
        call(disconnect),
    ]

    with pytest.raises(ManagementConnectionError):
        await task


async def test_nm_individual_address_write_address_found_other_in_programming_mode(
    time_travel,
):
    """Test nm_individual_address_write."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("1.1.5")
    individual_address_pgm = IndividualAddress("1.1.4")

    connect = Telegram(destination_address=individual_address, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    ack = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    ack2 = Telegram(
        source_address=IndividualAddress(0),
        destination_address=individual_address,
        tpci=tpci.TAck(0),
    )
    device_desc_resp = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorResponse(),
    )
    disconnect = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDisconnect(),
    )
    individual_address_read = Telegram(
        GroupAddress("0/0/0"), payload=apci.IndividualAddressRead()
    )
    address_reply_message = Telegram(
        source_address=individual_address_pgm,
        destination_address=GroupAddress("0/0/0"),
        direction=TelegramDirection.INCOMING,
        payload=apci.IndividualAddressResponse(),
    )

    task = asyncio.create_task(
        procedures.nm_individual_address_write(
            xknx=xknx, individual_address=individual_address
        )
    )

    # make sure first request (address check) times out
    await time_travel(0)
    xknx.management.process(ack)
    xknx.management.process(device_desc_resp)
    await time_travel(MANAGAMENT_CONNECTION_TIMEOUT)

    xknx.management.process(address_reply_message)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
        call(ack2),
        call(disconnect),
        call(individual_address_read),
    ]

    with pytest.raises(ManagementConnectionError):
        await task


async def test_nm_individual_address_serial_number_read(time_travel):
    """Test nm_individual_address_serial_number_read."""

    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("1.1.5")
    serial_number = b"aabbccddeeff"

    task = asyncio.create_task(
        procedures.nm_individual_address_serial_number_read(
            xknx=xknx, serial=serial_number
        )
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


async def test_nm_individual_address_serial_number_read_fail(time_travel):
    """Test nm_individual_address_serial_number_read."""

    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    serial_number = b"aabbccddeeff"

    task = asyncio.create_task(
        procedures.nm_individual_address_serial_number_read(
            xknx=xknx, serial=serial_number
        )
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


async def test_nm_individual_address_serial_number_write(time_travel):
    """Test nm_individual_address_serial_number_write."""

    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    serial_number = b"aabbccddeeff"
    individual_address = IndividualAddress("1.1.5")

    task = asyncio.create_task(
        procedures.nm_individual_address_serial_number_write(
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


async def test_nm_individual_address_serial_number_write_fail_no_response(time_travel):
    """Test nm_individual_address_serial_number_write."""

    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    serial_number = b"aabbccddeeff"
    individual_address = IndividualAddress("1.1.5")

    task = asyncio.create_task(
        procedures.nm_individual_address_serial_number_write(
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

    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(write_address),
        call(read_address),
    ]
    await time_travel(3)
    with pytest.raises(ManagementConnectionError):
        await task


async def test_nm_individual_address_serial_number_write_fail_wrong_address(
    time_travel,
):
    """Test nm_individual_address_serial_number_write."""

    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    serial_number = b"aabbccddeeff"
    individual_address_tx = IndividualAddress("1.1.5")
    individual_address_rx = IndividualAddress("1.1.6")

    task = asyncio.create_task(
        procedures.nm_individual_address_serial_number_write(
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
