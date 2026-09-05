"""Tests for dmp_mem_write_extended_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.22."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_mem_write_extended_r import (
    dmp_mem_write_extended_r,
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


def _response(
    address: int, return_code: int = 0, confirmation_data: bytes = b""
) -> apci.MemoryExtendedWriteResponse:
    """Build a MemoryExtendedWriteResponse."""
    return apci.MemoryExtendedWriteResponse(
        return_code=return_code, address=address, confirmation_data=confirmation_data
    )


async def test_dmp_mem_write_extended_r_basic(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_extended_r writes a single chunk fitting the default APDU length."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(xknx, ia, seq=0, payload=_response(0x100000))

    responder = asyncio.create_task(respond())
    await dmp_mem_write_extended_r(conn, address=0x100000, data=b"\x01\x02\x03")
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list[0].args[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.MemoryExtendedWrite(address=0x100000, data=b"\x01\x02\x03"),
    )
    await conn.disconnect()


async def test_dmp_mem_write_extended_r_success_with_crc_accepted(
    xknx_setup: XKNX,
) -> None:
    """
    Test dmp_mem_write_extended_r accepts E_SUCCESS_WITH_CRC (01h) as success.

    KNX v02.01.01 - Application Layer 03.03.07 - §3.4.9.2.1, Table 4: a
    device may confirm a write with this return code instead of a bare
    E_SUCCESS, carrying a CRC16-CCITT as confirmation_data.
    """
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
            payload=_response(
                0x100000, return_code=0x01, confirmation_data=b"\x12\x34"
            ),
        )

    responder = asyncio.create_task(respond())
    await dmp_mem_write_extended_r(conn, address=0x100000, data=b"\x01\x02\x03")
    await responder

    await conn.disconnect()


async def test_dmp_mem_write_extended_r_chunked(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_extended_r splits a write exceeding the wire chunk size."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(xknx, ia, seq=0, payload=_response(0x100000))
        await _wait_for_request(xknx, 2)
        _process_response(xknx, ia, seq=1, payload=_response(0x10000A))

    responder = asyncio.create_task(respond())
    # default max_apdu_length=15 -> 15 - 5 (header) = 10 octets per chunk
    await dmp_mem_write_extended_r(conn, address=0x100000, data=b"\x01" * 13)
    await responder

    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(0),
            payload=apci.MemoryExtendedWrite(address=0x100000, data=b"\x01" * 10),
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(1),
            payload=apci.MemoryExtendedWrite(address=0x10000A, data=b"\x01" * 3),
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
    ]
    await conn.disconnect()


async def test_dmp_mem_write_extended_r_empty_data(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_extended_r sends nothing for empty data."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    await dmp_mem_write_extended_r(conn, address=0x100000, data=b"")

    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dmp_mem_write_extended_r_address_out_of_range(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_extended_r raises ValueError for an address outside 0-16777215."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"address must be 0-16777215, got 16777216"):
        await dmp_mem_write_extended_r(conn, address=0x1000000, data=b"\x01")
    await conn.disconnect()


async def test_dmp_mem_write_extended_r_range_out_of_bounds(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_extended_r raises ValueError when address + len(data) - 1 overflows 0xFFFFFF."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(
        ValueError, match=r"address \+ len\(data\) - 1 must be <= 0xffffff"
    ):
        await dmp_mem_write_extended_r(conn, address=0xFFFFFF, data=b"\x01\x02")
    await conn.disconnect()


async def test_dmp_mem_write_extended_r_max_apdu_length_not_positive(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_mem_write_extended_r raises ValueError for max_apdu_length <= 0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"max_apdu_length must be positive, got 0"):
        await dmp_mem_write_extended_r(
            conn, address=0x100000, data=b"\x01", max_apdu_length=0
        )
    await conn.disconnect()


async def test_dmp_mem_write_extended_r_no_room_for_data(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_extended_r raises ValueError when max_apdu_length leaves no room for data."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"leaves no room for memory data"):
        await dmp_mem_write_extended_r(
            conn, address=0x100000, data=b"\x01", max_apdu_length=5
        )
    await conn.disconnect()


async def test_dmp_mem_write_extended_r_negative_return_code_raises(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_mem_write_extended_r raises when the response carries a negative return code."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx, ia, seq=0, payload=_response(0x100000, return_code=0xF1)
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"return code 0xf1"):
        await dmp_mem_write_extended_r(conn, address=0x100000, data=b"\x01\x02\x03")
    await responder

    await conn.disconnect()


async def test_dmp_mem_write_extended_r_wrong_address_echoed(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_extended_r raises when a response echoes a different address."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(xknx, ia, seq=0, payload=_response(0x200000))

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"response echoed 0x200000"):
        await dmp_mem_write_extended_r(conn, address=0x100000, data=b"\x01\x02\x03")
    await responder

    await conn.disconnect()
