"""Tests for dmp_prog_mode_switch_r_co — KNX v02.01.02 - Management Procedures 03.05.02 - §3.13.2."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_prog_mode_switch_r_co import (
    dmp_prog_mode_switch_r_co,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


def _xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _read_request(ia: IndividualAddress, sequence: int) -> Telegram:
    """Build the outgoing MemoryRead telegram for curr_prog_mode."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(sequence),
        payload=apci.MemoryRead(address=0x0060, count=1),
    )


def _write_request(ia: IndividualAddress, sequence: int, data: bytes) -> Telegram:
    """Build the outgoing MemoryWrite telegram for curr_prog_mode."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(sequence),
        payload=apci.MemoryWrite(address=0x0060, data=data),
    )


def _ack(ia: IndividualAddress, xknx: XKNX, sequence: int) -> Telegram:
    """Build an incoming TAck for a given sequence number."""
    return Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(sequence),
    )


def _read_response(
    ia: IndividualAddress, xknx: XKNX, sequence: int, data: bytes
) -> Telegram:
    """Build an incoming MemoryResponse telegram."""
    return Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(sequence),
        payload=apci.MemoryResponse(address=0x0060, data=data),
    )


async def test_dmp_prog_mode_switch_r_co_off_to_on_toggles_parity() -> None:
    """Test switching from off to on sets bit 0 and inverts the parity bit."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dmp_prog_mode_switch_r_co(conn, mode=True))
    await asyncio.sleep(0)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(_read_request(ia, 0))
    ]

    xknx.management.process(_ack(ia, xknx, 0))
    # current = 0b0101_0100: prog_mode=0, parity=0, don't-care bits = 0b101010
    xknx.management.process(_read_response(ia, xknx, 0, data=bytes([0b0101_0100])))
    await asyncio.sleep(0)
    xknx.management.process(_ack(ia, xknx, 1))

    await task

    # prog_mode set to 1, parity inverted to 1, don't-care bits unchanged
    assert xknx.cemi_handler.send_telegram.call_args_list[-1] == call(
        _write_request(ia, 1, data=bytes([0b1101_0101]))
    )

    await conn.disconnect()


async def test_dmp_prog_mode_switch_r_co_on_to_off_toggles_parity() -> None:
    """Test switching from on to off clears bit 0 and inverts the parity bit."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dmp_prog_mode_switch_r_co(conn, mode=False))
    await asyncio.sleep(0)

    xknx.management.process(_ack(ia, xknx, 0))
    # current = 0b1101_0101: prog_mode=1, parity=1, don't-care bits = 0b101010
    xknx.management.process(_read_response(ia, xknx, 0, data=bytes([0b1101_0101])))
    await asyncio.sleep(0)
    xknx.management.process(_ack(ia, xknx, 1))

    await task

    # prog_mode cleared to 0, parity inverted to 0, don't-care bits unchanged
    assert xknx.cemi_handler.send_telegram.call_args_list[-1] == call(
        _write_request(ia, 1, data=bytes([0b0101_0100]))
    )

    await conn.disconnect()


async def test_dmp_prog_mode_switch_r_co_same_mode_leaves_parity_unchanged() -> None:
    """Test requesting the mode the device already reports doesn't touch the parity bit."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dmp_prog_mode_switch_r_co(conn, mode=True))
    await asyncio.sleep(0)

    xknx.management.process(_ack(ia, xknx, 0))
    # already on: prog_mode=1, parity=1
    xknx.management.process(_read_response(ia, xknx, 0, data=bytes([0b1101_0101])))
    await asyncio.sleep(0)
    xknx.management.process(_ack(ia, xknx, 1))

    await task

    # unchanged: same byte written back
    assert xknx.cemi_handler.send_telegram.call_args_list[-1] == call(
        _write_request(ia, 1, data=bytes([0b1101_0101]))
    )

    await conn.disconnect()


async def test_dmp_prog_mode_switch_r_co_wrong_address_raises() -> None:
    """Test the procedure raises when the read response echoes a different address."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dmp_prog_mode_switch_r_co(conn, mode=True))
    await asyncio.sleep(0)

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(0),
            payload=apci.MemoryResponse(address=0x0061, data=bytes([0])),
        )
    )

    with pytest.raises(ManagementConnectionError, match=r"response echoed 0x0061"):
        await task

    await conn.disconnect()


async def test_dmp_prog_mode_switch_r_co_wrong_length_raises() -> None:
    """Test the procedure raises when the read response doesn't carry exactly 1 octet."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dmp_prog_mode_switch_r_co(conn, mode=True))
    await asyncio.sleep(0)

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(_read_response(ia, xknx, 0, data=b""))

    with pytest.raises(
        ManagementConnectionError, match=r"returned 0 octets, expected 1"
    ):
        await task

    await conn.disconnect()
