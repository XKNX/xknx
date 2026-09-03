"""Tests for dmp_mem_read_r_co — KNX v02.01.02 - Management Procedures 03.05.02 - §3.18.2."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_mem_read_r_co import dmp_mem_read_r_co
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


async def test_dmp_mem_read_r_co_basic(xknx_setup: XKNX) -> None:
    """Test dmp_mem_read_r_co reads a single chunk fitting the default APDU length."""
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
            payload=apci.MemoryResponse(address=0x1000, data=b"\x01\x02\x03"),
        )

    responder = asyncio.create_task(respond())
    data = await dmp_mem_read_r_co(conn, address=0x1000, size=3)
    await responder

    assert data == b"\x01\x02\x03"
    assert xknx.cemi_handler.send_telegram.call_args_list[0].args[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.MemoryRead(address=0x1000, count=3),
    )
    await conn.disconnect()


async def test_dmp_mem_read_r_co_chunked(xknx_setup: XKNX) -> None:
    """Test dmp_mem_read_r_co splits a read exceeding the wire chunk size."""
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
            payload=apci.MemoryResponse(address=0x1000, data=b"\x01" * 12),
        )
        await _wait_for_request(xknx, 2)
        _process_response(
            xknx,
            ia,
            seq=1,
            payload=apci.MemoryResponse(address=0x100C, data=b"\x02" * 3),
        )

    responder = asyncio.create_task(respond())
    # default max_apdu_length=15 -> 15 - 3 (header) = 12 octets per chunk
    data = await dmp_mem_read_r_co(conn, address=0x1000, size=15)
    await responder

    assert data == b"\x01" * 12 + b"\x02" * 3
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(0),
            payload=apci.MemoryRead(address=0x1000, count=12),
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(1),
            payload=apci.MemoryRead(address=0x100C, count=3),
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
    ]
    await conn.disconnect()


async def test_dmp_mem_read_r_co_zero_size(xknx_setup: XKNX) -> None:
    """Test dmp_mem_read_r_co returns empty bytes without sending anything for size=0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    data = await dmp_mem_read_r_co(conn, address=0x1000, size=0)

    assert data == b""
    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dmp_mem_read_r_co_negative_size(xknx_setup: XKNX) -> None:
    """Test dmp_mem_read_r_co raises ValueError for a negative size."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"size must be >= 0, got -1"):
        await dmp_mem_read_r_co(conn, address=0x1000, size=-1)
    await conn.disconnect()


async def test_dmp_mem_read_r_co_address_out_of_range(xknx_setup: XKNX) -> None:
    """Test dmp_mem_read_r_co raises ValueError for an address outside 0-65535."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"address must be 0-65535, got 65536"):
        await dmp_mem_read_r_co(conn, address=0x10000, size=1)
    await conn.disconnect()


async def test_dmp_mem_read_r_co_max_apdu_length_not_positive(xknx_setup: XKNX) -> None:
    """Test dmp_mem_read_r_co raises ValueError for max_apdu_length <= 0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"max_apdu_length must be positive, got 0"):
        await dmp_mem_read_r_co(conn, address=0x1000, size=1, max_apdu_length=0)
    await conn.disconnect()


async def test_dmp_mem_read_r_co_no_room_for_data(xknx_setup: XKNX) -> None:
    """Test dmp_mem_read_r_co raises ValueError when max_apdu_length leaves no room for data."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"leaves no room for memory data"):
        await dmp_mem_read_r_co(conn, address=0x1000, size=1, max_apdu_length=3)
    await conn.disconnect()


async def test_dmp_mem_read_r_co_error_short_response(xknx_setup: XKNX) -> None:
    """Test dmp_mem_read_r_co raises when a chunk's response is shorter than requested."""
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
            payload=apci.MemoryResponse(address=0x1000, data=b"\x01\x02"),  # asked 3
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"requested 3 octets, got 2"):
        await dmp_mem_read_r_co(conn, address=0x1000, size=3)
    await responder

    await conn.disconnect()
