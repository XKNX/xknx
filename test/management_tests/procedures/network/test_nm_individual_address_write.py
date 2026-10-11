"""Tests for nm_individual_address_write — KNX v02.01.02 - Management Procedures 03.05.02 - §2.3 NM_IndividualAddress_Write."""

import asyncio
import importlib
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import MANAGEMENT_CONNECTION_TIMEOUT
from xknx.management.procedures.network.nm_individual_address_write import (
    PROGRAMMING_MODE_POLL_TIMEOUT,
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

# The package re-exports the procedure under the module's name, so import the module itself.
procedure_module = importlib.import_module(
    "xknx.management.procedures.network.nm_individual_address_write"
)


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

    # make sure first request (address check) times out
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)

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


async def test_nm_individual_address_write_address_occupied_by_disconnect(
    time_travel: EventLoopClockAdvancer,
) -> None:
    """
    Test nm_individual_address_write when device refuses connection during address check.

    Device sends TDisconnect → nm_individual_address_check(xknx, address) already handles
    this internally (its own connection context manager's finally raises
    ManagementConnectionRefused from disconnect() after the peer already disconnected, and its
    own except swallows it) → returns True.
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
    ack_from_device = Telegram(
        source_address=individual_address,
        destination_address=IndividualAddress(0),
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
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

    # device sends disconnect (address occupied) then ACK for the DeviceDescriptorRead
    xknx.management.process(disconnect_from_device)
    xknx.management.process(ack_from_device)

    # nm_individual_address_check's own connection context manager finally raises
    # ManagementConnectionRefused (peer already disconnected, no TDisconnect sent by us);
    # its own except swallows it and returns True; IndividualAddressRead broadcast is sent
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

    # make sure first request (address check) times out
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)

    # send response to device in programming mode
    xknx.management.process(address_reply_message)

    # device experienced error, so set connection request timeout
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)

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


class _FakeConnection:
    async def __aenter__(self) -> "_FakeConnection":
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


def _patch_bus(
    monkeypatch: pytest.MonkeyPatch, responses: list[list[IndividualAddress]]
) -> tuple[XKNX, list[float | None]]:
    """Fake a bus with a free target address whose devices answer ``responses`` in turn."""
    timeouts: list[float | None] = []

    async def fake_check(xknx: XKNX, individual_address: IndividualAddress) -> bool:
        return False

    async def fake_read(
        xknx: XKNX, timeout: float | None = 3, raise_if_multiple: bool = False
    ) -> list[IndividualAddress]:
        timeouts.append(timeout)
        await asyncio.sleep(timeout or 0)
        return responses.pop(0) if responses else []

    async def fake_check_conn(conn: object) -> bool:
        return True

    async def fake_restart(conn: object) -> None:
        return None

    monkeypatch.setattr(procedure_module, "nm_individual_address_check", fake_check)
    monkeypatch.setattr(procedure_module, "nm_individual_address_read", fake_read)
    monkeypatch.setattr(
        procedure_module, "nm_individual_address_check_conn", fake_check_conn
    )
    monkeypatch.setattr(procedure_module, "dm_restart_r_co", fake_restart)
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    monkeypatch.setattr(
        type(xknx.management), "connection", lambda self, address: _FakeConnection()
    )
    return xknx, timeouts


def _address_writes(xknx: XKNX) -> list[IndividualAddress]:
    """Return the addresses broadcast with A_IndividualAddress_Write."""
    return [
        c.args[0].payload.address
        for c in xknx.cemi_handler.send_telegram.call_args_list
        if isinstance(c.args[0].payload, apci.IndividualAddressWrite)
    ]


async def test_nm_individual_address_write_waits_for_programming_mode(
    monkeypatch: pytest.MonkeyPatch, time_travel: EventLoopClockAdvancer
) -> None:
    """Test A_IndividualAddress_Read is repeated until a device is in programming mode."""
    xknx, timeouts = _patch_bus(monkeypatch, [[], [], [IndividualAddress("15.15.255")]])

    task = asyncio.create_task(
        nm_individual_address_write(xknx, "1.1.4", wait_for_programming_mode=10)
    )
    for _ in range(3):
        await time_travel(PROGRAMMING_MODE_POLL_TIMEOUT)
    await task

    assert timeouts == [PROGRAMMING_MODE_POLL_TIMEOUT] * 3
    assert _address_writes(xknx) == [IndividualAddress("1.1.4")]


async def test_nm_individual_address_write_wait_times_out(
    monkeypatch: pytest.MonkeyPatch, time_travel: EventLoopClockAdvancer
) -> None:
    """Test waiting for programming mode ends after ``wait_for_programming_mode``."""
    xknx, timeouts = _patch_bus(monkeypatch, [])

    task = asyncio.create_task(
        nm_individual_address_write(xknx, "1.1.4", wait_for_programming_mode=2.5)
    )
    for _ in range(3):
        await time_travel(PROGRAMMING_MODE_POLL_TIMEOUT)
    with pytest.raises(
        ManagementConnectionError, match="No device in programming mode"
    ):
        await task

    assert len(timeouts) == 3
    assert _address_writes(xknx) == []


async def test_nm_individual_address_write_reads_once_by_default(
    monkeypatch: pytest.MonkeyPatch, time_travel: EventLoopClockAdvancer
) -> None:
    """Test without ``wait_for_programming_mode`` programming mode is read once."""
    xknx, timeouts = _patch_bus(monkeypatch, [])

    task = asyncio.create_task(nm_individual_address_write(xknx, "1.1.4"))
    await time_travel(3)
    with pytest.raises(
        ManagementConnectionError, match="No device in programming mode"
    ):
        await task

    assert timeouts == [3]
