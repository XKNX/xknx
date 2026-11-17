"""Tests for dmp_prog_mode_switch_r_co — KNX v02.01.02 - Management Procedures 03.05.02 - §3.13.2."""

import asyncio
from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.procedures.device.dmp_prog_mode_switch_r_co import (
    _PROG_MODE_ADDRESS,
    dm_prog_mode_switch,
    dmp_prog_mode_switch_r_co,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci

RESPONDER_TIMEOUT = 1


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _process(
    xknx: XKNX,
    ia: IndividualAddress,
    ack_seq: int,
    payload: apci.APCI | None = None,
    response_seq: int = 0,
) -> None:
    """Inject the device's ACK (+ optional TDataConnected response) into the management layer."""
    xknx.management.process(
        Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(ack_seq),
        )
    )
    if payload is not None:
        xknx.management.process(
            Telegram(
                source_address=ia,
                destination_address=xknx.current_address,
                direction=TelegramDirection.INCOMING,
                tpci=tpci.TDataConnected(response_seq),
                payload=payload,
            )
        )


async def _wait_for_calls(xknx: XKNX, count: int) -> None:
    """Wait until at least count telegrams have been sent."""
    async with asyncio.timeout(RESPONDER_TIMEOUT):
        while xknx.cemi_handler.send_telegram.call_count < count:  # noqa: ASYNC110
            await asyncio.sleep(0)


def _read(ia: IndividualAddress, seq: int = 0) -> Telegram:
    """Return the A_Memory_Read of curr_prog_mode."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(seq),
        payload=apci.MemoryRead(address=_PROG_MODE_ADDRESS, count=1),
    )


def _write(ia: IndividualAddress, value: int, seq: int = 1) -> Telegram:
    """Return the A_Memory_Write of curr_prog_mode."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(seq),
        payload=apci.MemoryWrite(address=_PROG_MODE_ADDRESS, data=bytes([value])),
    )


def _descriptor_read(ia: IndividualAddress) -> Telegram:
    """Return the A_DeviceDescriptor_Read of DD0 that DM_Connect sends."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )


def _descriptor(mask_version: int) -> apci.DeviceDescriptorResponse:
    """Return the A_DeviceDescriptor_Response carrying the mask version."""
    return apci.DeviceDescriptorResponse(descriptor=0, value=mask_version)


def _response(value: int) -> apci.MemoryResponse:
    """Return the A_Memory_Response carrying curr_prog_mode."""
    return apci.MemoryResponse(address=_PROG_MODE_ADDRESS, data=bytes([value]))


@pytest.mark.parametrize(
    ("current", "mode", "written"),
    [
        # prog_mode set, p_parity inverted, shared bits 1-6 kept
        (0x2E, True, 0xAF),
        (0xAF, False, 0x2E),
        (0x00, True, 0x81),
        (0x81, False, 0x00),
    ],
)
async def test_dmp_prog_mode_switch_r_co(
    xknx_setup: XKNX, current: int, mode: bool, written: int
) -> None:
    """Test curr_prog_mode is read at 60h and written back with prog_mode and parity."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process(xknx, ia, ack_seq=0, payload=_response(current))
        await _wait_for_calls(xknx, 3)
        _process(xknx, ia, ack_seq=1)

    responder = asyncio.create_task(respond())
    await dmp_prog_mode_switch_r_co(conn, mode)
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(_read(ia)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(0))),
        call(_write(ia, written)),
    ]
    await conn.disconnect()


@pytest.mark.parametrize(
    ("current", "mode"),
    [
        (0x81, True),
        (0x2E, False),
    ],
)
async def test_dmp_prog_mode_switch_r_co_unchanged(
    xknx_setup: XKNX, current: int, mode: bool
) -> None:
    """Test nothing is written when prog_mode already matches mode."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process(xknx, ia, ack_seq=0, payload=_response(current))

    responder = asyncio.create_task(respond())
    await dmp_prog_mode_switch_r_co(conn, mode)
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(_read(ia)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(0))),
    ]
    await conn.disconnect()


async def test_dmp_prog_mode_switch_r_co_no_data(xknx_setup: XKNX) -> None:
    """Test a read answered without data raises and writes nothing."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process(
            xknx,
            ia,
            ack_seq=0,
            payload=apci.MemoryResponse(address=_PROG_MODE_ADDRESS, data=b""),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError):
        await dmp_prog_mode_switch_r_co(conn, True)
    await responder

    assert not any(
        isinstance(c.args[0].payload, apci.MemoryWrite)
        for c in xknx.cemi_handler.send_telegram.call_args_list
    )
    await conn.disconnect()


async def test_dmp_prog_mode_switch_r_co_verify(xknx_setup: XKNX) -> None:
    """Test verify reads curr_prog_mode back after writing it."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process(xknx, ia, ack_seq=0, payload=_response(0x2E))
        await _wait_for_calls(xknx, 3)
        _process(xknx, ia, ack_seq=1)
        await _wait_for_calls(xknx, 4)
        _process(xknx, ia, ack_seq=2, payload=_response(0xAF), response_seq=1)

    responder = asyncio.create_task(respond())
    await dmp_prog_mode_switch_r_co(conn, True, verify=True)
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(_read(ia)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(0))),
        call(_write(ia, 0xAF)),
        call(_read(ia, seq=2)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(1))),
    ]
    await conn.disconnect()


async def test_dmp_prog_mode_switch_r_co_verify_rejected(xknx_setup: XKNX) -> None:
    """Test verify raises when the device kept its old curr_prog_mode."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process(xknx, ia, ack_seq=0, payload=_response(0x2E))
        await _wait_for_calls(xknx, 3)
        _process(xknx, ia, ack_seq=1)
        await _wait_for_calls(xknx, 4)
        _process(xknx, ia, ack_seq=2, payload=_response(0x2E), response_seq=1)

    responder = asyncio.create_task(respond())
    with pytest.raises(VerificationError):
        await dmp_prog_mode_switch_r_co(conn, True, verify=True)
    await responder
    await conn.disconnect()


async def _switch_memory(
    xknx: XKNX,
    ia: IndividualAddress,
    switch: Callable[[XKNX, IndividualAddress, bool], Awaitable[None]],
    mask_version: int,
) -> None:
    """Run ``switch`` against a device answering DD0 and curr_prog_mode 2Eh."""

    async def respond() -> None:
        await _wait_for_calls(xknx, 2)
        _process(xknx, ia, ack_seq=0, payload=_descriptor(mask_version))
        await _wait_for_calls(xknx, 4)
        _process(xknx, ia, ack_seq=1, payload=_response(0x2E), response_seq=1)
        await _wait_for_calls(xknx, 6)
        _process(xknx, ia, ack_seq=2)

    responder = asyncio.create_task(respond())
    await switch(xknx, ia, True)
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(Telegram(destination_address=ia, tpci=tpci.TConnect())),
        call(_descriptor_read(ia)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(0))),
        call(_read(ia, seq=1)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(1))),
        call(_write(ia, 0xAF, seq=2)),
        call(Telegram(destination_address=ia, tpci=tpci.TDisconnect())),
    ]


@pytest.mark.parametrize("mask_version", [0x0705, 0x07B0, 0x0BAD])
async def test_dm_prog_mode_switch(xknx_setup: XKNX, mask_version: int) -> None:
    """Test dm_prog_mode_switch switches memory 60h, whatever the mask version."""
    await _switch_memory(
        xknx_setup, IndividualAddress("4.0.10"), dm_prog_mode_switch, mask_version
    )


async def test_dm_prog_mode_switch_unchanged(xknx_setup: XKNX) -> None:
    """Test dm_prog_mode_switch writes nothing when prog_mode already matches."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    async def respond() -> None:
        await _wait_for_calls(xknx, 2)
        _process(xknx, ia, ack_seq=0, payload=_descriptor(0x0705))
        await _wait_for_calls(xknx, 4)
        _process(xknx, ia, ack_seq=1, payload=_response(0x2E), response_seq=1)

    responder = asyncio.create_task(respond())
    await dm_prog_mode_switch(xknx, ia, False)
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(Telegram(destination_address=ia, tpci=tpci.TConnect())),
        call(_descriptor_read(ia)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(0))),
        call(_read(ia, seq=1)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(1))),
        call(Telegram(destination_address=ia, tpci=tpci.TDisconnect())),
    ]
