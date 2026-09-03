"""Tests for dmp_user_mem_write_r_co — KNX v02.01.02 - Management Procedures 03.05.02 - §3.19.2."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_user_mem_write_r_co import (
    dmp_user_mem_write_r_co,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci

RESPONDER_TIMEOUT = 1


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _process_response(
    xknx: XKNX,
    ia: IndividualAddress,
    ack_seq: int,
    payload: apci.APCI | None = None,
    response_seq: int = 0,
) -> None:
    """Inject ACK (+ optional TDataConnected response) into the management layer."""
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


async def test_dmp_user_mem_write_r_co_no_verify(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_write_r_co writes without a read-back, waiting only for the ACK."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process_response(xknx, ia, ack_seq=0)

    responder = asyncio.create_task(respond())
    await dmp_user_mem_write_r_co(conn, address=0xF0000, data=b"\x01\x02\x03")
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(
            Telegram(
                destination_address=ia,
                tpci=tpci.TDataConnected(0),
                payload=apci.UserMemoryWrite(address=0xF0000, data=b"\x01\x02\x03"),
            )
        )
    ]
    await conn.disconnect()


async def test_dmp_user_mem_write_r_co_chunked(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_write_r_co splits a write exceeding the wire chunk size."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process_response(xknx, ia, ack_seq=0)
        await _wait_for_calls(xknx, 2)
        _process_response(xknx, ia, ack_seq=1)

    responder = asyncio.create_task(respond())
    # default max_apdu_length=15 -> 15 - 4 (header) = 11 octets per chunk
    await dmp_user_mem_write_r_co(conn, address=0x1000, data=b"\x01" * 14)
    await responder

    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(0),
            payload=apci.UserMemoryWrite(address=0x1000, data=b"\x01" * 11),
        ),
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(1),
            payload=apci.UserMemoryWrite(address=0x100B, data=b"\x01" * 3),
        ),
    ]
    await conn.disconnect()


async def test_dmp_user_mem_write_r_co_verify_success(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_write_r_co with verify=True reads back and compares each chunk."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process_response(xknx, ia, ack_seq=0)
        await _wait_for_calls(xknx, 2)
        _process_response(
            xknx,
            ia,
            ack_seq=1,
            payload=apci.UserMemoryResponse(address=0x1000, data=b"\x01\x02\x03"),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    await dmp_user_mem_write_r_co(
        conn, address=0x1000, data=b"\x01\x02\x03", verify=True
    )
    await responder

    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(0),
            payload=apci.UserMemoryWrite(address=0x1000, data=b"\x01\x02\x03"),
        ),
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(1),
            payload=apci.UserMemoryRead(address=0x1000, count=3),
        ),
        # our ACK of the device's incoming UserMemoryResponse (response_seq=0)
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
    ]
    await conn.disconnect()


async def test_dmp_user_mem_write_r_co_verify_mismatch(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_write_r_co with verify=True raises when the read-back differs."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process_response(xknx, ia, ack_seq=0)
        await _wait_for_calls(xknx, 2)
        _process_response(
            xknx,
            ia,
            ack_seq=1,
            payload=apci.UserMemoryResponse(address=0x1000, data=b"\xff\xff\xff"),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"User memory verify failed"):
        await dmp_user_mem_write_r_co(
            conn, address=0x1000, data=b"\x01\x02\x03", verify=True
        )
    await responder

    await conn.disconnect()


async def test_dmp_user_mem_write_r_co_empty_data(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_write_r_co is a no-op for empty data."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    await dmp_user_mem_write_r_co(conn, address=0x1000, data=b"")

    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dmp_user_mem_write_r_co_address_out_of_range(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_write_r_co raises ValueError for an address outside 0-0xFFFFF."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"address must be 0-0xFFFFF, got 1048576"):
        await dmp_user_mem_write_r_co(conn, address=0x100000, data=b"\x01")
    await conn.disconnect()
