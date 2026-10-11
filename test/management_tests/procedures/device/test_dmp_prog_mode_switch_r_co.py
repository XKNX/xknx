"""Tests for dmp_prog_mode_switch_r_co — KNX v02.01.02 - Management Procedures 03.05.02 - §3.13.2."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_prog_mode_switch_r_co import (
    PROG_MODE_ADDRESS,
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
    xknx: XKNX, ia: IndividualAddress, ack_seq: int, payload: apci.APCI | None = None
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
                tpci=tpci.TDataConnected(0),
                payload=payload,
            )
        )


async def _wait_for_calls(xknx: XKNX, count: int) -> None:
    """Wait until at least count telegrams have been sent."""
    async with asyncio.timeout(RESPONDER_TIMEOUT):
        while xknx.cemi_handler.send_telegram.call_count < count:  # noqa: ASYNC110
            await asyncio.sleep(0)


def _read(ia: IndividualAddress) -> Telegram:
    """Return the A_Memory_Read of curr_prog_mode."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.MemoryRead(address=PROG_MODE_ADDRESS, count=1),
    )


def _write(ia: IndividualAddress, value: int) -> Telegram:
    """Return the A_Memory_Write of curr_prog_mode."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(1),
        payload=apci.MemoryWrite(address=PROG_MODE_ADDRESS, data=bytes([value])),
    )


def _response(value: int) -> apci.MemoryResponse:
    """Return the A_Memory_Response carrying curr_prog_mode."""
    return apci.MemoryResponse(address=PROG_MODE_ADDRESS, data=bytes([value]))


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
            payload=apci.MemoryResponse(address=PROG_MODE_ADDRESS, data=b""),
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


async def test_dm_prog_mode_switch(xknx_setup: XKNX) -> None:
    """Test dm_prog_mode_switch opens and closes its own connection."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    async def respond() -> None:
        await _wait_for_calls(xknx, 2)
        _process(xknx, ia, ack_seq=0, payload=_response(0x2E))
        await _wait_for_calls(xknx, 4)
        _process(xknx, ia, ack_seq=1)

    responder = asyncio.create_task(respond())
    await dm_prog_mode_switch(xknx, ia, True)
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(Telegram(destination_address=ia, tpci=tpci.TConnect())),
        call(_read(ia)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(0))),
        call(_write(ia, 0xAF)),
        call(Telegram(destination_address=ia, tpci=tpci.TDisconnect())),
    ]


async def test_dm_prog_mode_switch_unchanged(xknx_setup: XKNX) -> None:
    """Test dm_prog_mode_switch writes nothing when prog_mode already matches."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    async def respond() -> None:
        await _wait_for_calls(xknx, 2)
        _process(xknx, ia, ack_seq=0, payload=_response(0x2E))

    responder = asyncio.create_task(respond())
    await dm_prog_mode_switch(xknx, ia, False)
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(Telegram(destination_address=ia, tpci=tpci.TConnect())),
        call(_read(ia)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(0))),
        call(Telegram(destination_address=ia, tpci=tpci.TDisconnect())),
    ]
