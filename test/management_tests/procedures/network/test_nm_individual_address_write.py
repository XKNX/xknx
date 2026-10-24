"""Tests for nm_individual_address_write — KNX v02.01.02 - Management Procedures 03.05.02 - §2.3 NM_IndividualAddress_Write."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import (
    MANAGEMENT_ACK_TIMEOUT,
    MANAGEMENT_CONNECTION_TIMEOUT,
    MANAGEMENT_MAX_REP_COUNT,
)
from xknx.management.procedures.network.nm_individual_address_write import (
    nm_individual_address_write,
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


async def test_nm_individual_address_write(time_travel: EventLoopClockAdvancer) -> None:
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
        nm_individual_address_write(xknx, individual_address_new)
    )

    # make sure first request (address check) times out - the telegram is
    # repeated 3 times, then the connection is closed
    for _ in range(MANAGEMENT_MAX_REP_COUNT + 1):
        await time_travel(MANAGEMENT_ACK_TIMEOUT)

    # send response to device in programming mode
    xknx.management.process(address_reply_message)

    # confirm device is up and running
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)
    xknx.management.process(ack)
    xknx.management.process(device_desc_resp)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
        call(device_desc_read),  # due to retransmit
        call(device_desc_read),
        call(device_desc_read),
        call(disconnect),
        call(individual_address_read),
        call(individual_address_write),
        call(connect),
        call(device_desc_read),
        call(ack2),
    ]

    await task


async def test_nm_individual_address_write_two_devices_in_programming_mode(
    time_travel: EventLoopClockAdvancer,
) -> None:
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
        nm_individual_address_write(xknx, individual_address_new)
    )

    # make sure first request (address check) times out
    await time_travel(0)  # start
    await time_travel(3)  # first timeout
    await time_travel(3)  # second timeout
    await time_travel(3)  # third timeout
    await time_travel(3)  # fourth timeout - the connection is closed

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
        call(device_desc_read),  # due to retransmit
        call(device_desc_read),
        call(device_desc_read),
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
    assert len(xknx.cemi_handler.send_telegram.call_args_list) == 7


async def test_nm_individual_address_write_no_device_programming_mode(
    time_travel: EventLoopClockAdvancer,
) -> None:
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
        nm_individual_address_write(xknx, individual_address_new)
    )

    # make sure first request (address check) times out
    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
    ]
    # first timeout - retransmit DeviceDescriptorRead, 3 times
    for repetition in range(2, 5):
        await time_travel(3)
        assert xknx.cemi_handler.send_telegram.call_args_list[repetition:] == [
            call(device_desc_read),
        ]
    # retries also timed out - connection closed
    await time_travel(3)
    assert xknx.cemi_handler.send_telegram.call_args_list[5:] == [
        call(disconnect),
        call(individual_address_read),
    ]
    # IndividualAddressRead also times out
    await time_travel(3)
    with pytest.raises(
        ManagementConnectionError, match="No device in programming mode"
    ):
        await task
    assert len(xknx.cemi_handler.send_telegram.call_args_list) == 7


async def test_nm_individual_address_write_address_occupied_by_disconnect(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """
    Test nm_individual_address_write when device refuses connection during address check.

    The device answers the DeviceDescriptorRead with a TDisconnect instead of an ACK.
    The pending request fails with ManagementConnectionRefused right away - the telegram
    is not repeated - and nm_individual_address_check treats that as "address occupied"
    (KNX v02.01.02 - Management Procedures 03.05.02 - §2.3 step 1) → returns True.
    """
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    individual_address = IndividualAddress("1.1.4")

    connect = Telegram(destination_address=individual_address, tpci=tpci.TConnect())
    device_desc_read = Telegram(
        destination_address=individual_address,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    disconnect_from_device = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDisconnect(),
    )
    individual_address_read = Telegram(
        GroupAddress("0/0/0"), payload=apci.IndividualAddressRead()
    )

    task = asyncio.create_task(nm_individual_address_write(xknx, individual_address))

    # advance until address check is awaiting ACK
    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
    ]

    # device sends disconnect (address occupied) instead of an ACK
    xknx.management.process(disconnect_from_device)

    # the address check reports the address as occupied without waiting for the
    # ACK timeout; no TDisconnect is sent by us; IndividualAddressRead broadcast is sent
    await time_travel(0)
    assert xknx.cemi_handler.send_telegram.call_args_list[2:] == [
        call(individual_address_read),
    ]

    # no device in programming mode → timeout → error
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)
    with pytest.raises(
        ManagementConnectionError, match="No device in programming mode"
    ):
        await task
    assert len(xknx.cemi_handler.send_telegram.call_args_list) == 3


async def test_nm_individual_address_write_address_found(
    time_travel: EventLoopClockAdvancer,
) -> None:
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

    task = asyncio.create_task(nm_individual_address_write(xknx, individual_address))

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


async def test_nm_individual_address_write_programming_failed(
    time_travel: EventLoopClockAdvancer,
) -> None:
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
        nm_individual_address_write(xknx, individual_address_new)
    )

    # make sure first request (address check) times out - the telegram is
    # repeated 3 times, then the connection is closed
    for _ in range(MANAGEMENT_MAX_REP_COUNT + 1):
        await time_travel(MANAGEMENT_ACK_TIMEOUT)

    # send response to device in programming mode
    xknx.management.process(address_reply_message)

    # device experienced error, so the check after the write times out as well
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)
    for _ in range(MANAGEMENT_MAX_REP_COUNT + 1):
        await time_travel(MANAGEMENT_ACK_TIMEOUT)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
        call(device_desc_read),  # due to retransmit
        call(device_desc_read),
        call(device_desc_read),
        call(disconnect),
        call(individual_address_read),
        call(individual_address_write),
        call(connect),
        call(device_desc_read),
        call(device_desc_read),
        call(device_desc_read),
        call(device_desc_read),
        call(disconnect),
    ]

    with pytest.raises(ManagementConnectionError):
        await task


async def test_nm_individual_address_write_address_found_other_in_programming_mode(
    time_travel: EventLoopClockAdvancer,
) -> None:
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

    task = asyncio.create_task(nm_individual_address_write(xknx, individual_address))

    # first request (address check) succeeds
    await time_travel(0)
    xknx.management.process(ack)
    xknx.management.process(device_desc_resp)
    await time_travel(0)

    # a different device answers the programming-mode broadcast before its
    # 3s window elapses, so dev_pgm_mode[0] != individual_address
    xknx.management.process(address_reply_message)
    # fast-forward past the broadcast's 3s timeout via the mocked clock,
    # instead of waiting on it for real
    await time_travel(3)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(connect),
        call(device_desc_read),
        call(ack2),
        call(disconnect),
        call(individual_address_read),
    ]

    with pytest.raises(
        ManagementConnectionError,
        match=f"A device was found with {individual_address}, cannot continue with programming.",
    ):
        await task
