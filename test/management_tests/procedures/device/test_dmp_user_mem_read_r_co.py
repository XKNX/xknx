"""Tests for dmp_user_mem_read_r_co — KNX v02.01.02 - Management Procedures 03.05.02 - §3.21.2."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_user_mem_read_r_co import (
    dmp_user_mem_read_r_co,
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
    xknx: XKNX, ia: IndividualAddress, seq: int, payload: apci.APCI
) -> None:
    """Inject ACK + TDataConnected response into the management layer."""
    xknx.management.process(
        Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(seq),
        )
    )
    xknx.management.process(
        Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(seq),
            payload=payload,
        )
    )


async def _wait_for_request(xknx: XKNX, req_num: int) -> None:
    """Wait until the req_num-th request telegram has been sent (1-indexed)."""
    threshold = req_num * 2 - 1
    async with asyncio.timeout(RESPONDER_TIMEOUT):
        while xknx.cemi_handler.send_telegram.call_count < threshold:  # noqa: ASYNC110
            await asyncio.sleep(0)


async def test_dmp_user_mem_read_r_co_basic(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_read_r_co reads a single chunk fitting the default APDU length."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx,
            ia,
            seq=0,
            payload=apci.UserMemoryResponse(address=0xF0000, data=b"\x01\x02\x03"),
        )

    responder = asyncio.create_task(respond())
    data = await dmp_user_mem_read_r_co(conn, address=0xF0000, size=3)
    await responder

    assert data == b"\x01\x02\x03"
    assert xknx.cemi_handler.send_telegram.call_args_list[0].args[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.UserMemoryRead(address=0xF0000, count=3),
    )
    await conn.disconnect()


async def test_dmp_user_mem_read_r_co_chunked(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_read_r_co splits a read exceeding the wire chunk size."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx,
            ia,
            seq=0,
            payload=apci.UserMemoryResponse(address=0x1000, data=b"\x01" * 11),
        )
        await _wait_for_request(xknx, 2)
        _process_response(
            xknx,
            ia,
            seq=1,
            payload=apci.UserMemoryResponse(address=0x100B, data=b"\x02" * 3),
        )

    responder = asyncio.create_task(respond())
    # default max_apdu_length=15 -> 15 - 4 (header) = 11 octets per chunk
    data = await dmp_user_mem_read_r_co(conn, address=0x1000, size=14)
    await responder

    assert data == b"\x01" * 11 + b"\x02" * 3
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(0),
            payload=apci.UserMemoryRead(address=0x1000, count=11),
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(1),
            payload=apci.UserMemoryRead(address=0x100B, count=3),
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
    ]
    await conn.disconnect()


async def test_dmp_user_mem_read_r_co_zero_size(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_read_r_co returns empty bytes without sending anything for size=0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    data = await dmp_user_mem_read_r_co(conn, address=0x1000, size=0)

    assert data == b""
    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dmp_user_mem_read_r_co_negative_size(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_read_r_co raises ValueError for a negative size."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"size must be >= 0, got -1"):
        await dmp_user_mem_read_r_co(conn, address=0x1000, size=-1)
    await conn.disconnect()


async def test_dmp_user_mem_read_r_co_address_out_of_range(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_read_r_co raises ValueError for an address outside 0-0xFFFFF."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"address must be 0-0xFFFFF, got 1048576"):
        await dmp_user_mem_read_r_co(conn, address=0x100000, size=1)
    await conn.disconnect()


async def test_dmp_user_mem_read_r_co_range_out_of_bounds(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_read_r_co raises ValueError when address + size - 1 overflows 0xFFFFF."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"address \+ size - 1 must be <= 0xfffff"):
        await dmp_user_mem_read_r_co(conn, address=0xFFFFF, size=2)
    await conn.disconnect()


async def test_dmp_user_mem_read_r_co_max_apdu_length_not_positive(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_user_mem_read_r_co raises ValueError for max_apdu_length <= 0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"max_apdu_length must be positive, got 0"):
        await dmp_user_mem_read_r_co(conn, address=0x1000, size=1, max_apdu_length=0)
    await conn.disconnect()


async def test_dmp_user_mem_read_r_co_no_room_for_data(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_read_r_co raises ValueError when max_apdu_length leaves no room for data."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"leaves no room for memory data"):
        await dmp_user_mem_read_r_co(conn, address=0x1000, size=1, max_apdu_length=4)
    await conn.disconnect()


async def test_dmp_user_mem_read_r_co_error_short_response(xknx_setup: XKNX) -> None:
    """Test dmp_user_mem_read_r_co raises when a chunk's response is shorter than requested."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx,
            ia,
            seq=0,
            payload=apci.UserMemoryResponse(address=0x1000, data=b"\x01\x02"),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"requested 3 octets, got 2"):
        await dmp_user_mem_read_r_co(conn, address=0x1000, size=3)
    await responder

    await conn.disconnect()


async def test_dmp_user_mem_read_r_co_error_wrong_address_echoed(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_user_mem_read_r_co raises when a response echoes a different address."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx,
            ia,
            seq=0,
            payload=apci.UserMemoryResponse(address=0x2000, data=b"\x01\x02\x03"),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"response echoed 0x02000"):
        await dmp_user_mem_read_r_co(conn, address=0x1000, size=3)
    await responder

    await conn.disconnect()
