"""Tests for dmp_mem_verify_extended_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.23."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.procedures.device.dmp_mem_verify_extended_r import (
    dmp_mem_verify_extended_r,
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
    address: int, data: bytes, return_code: int = 0
) -> apci.MemoryExtendedReadResponse:
    """Build a MemoryExtendedReadResponse."""
    return apci.MemoryExtendedReadResponse(
        return_code=return_code, address=address, data=data
    )


async def test_dmp_mem_verify_extended_r_matches(xknx_setup: XKNX) -> None:
    """Test dmp_mem_verify_extended_r returns None when the read-back matches."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(xknx, ia, seq=0, payload=_response(0x100000, b"\x01\x02\x03"))

    responder = asyncio.create_task(respond())
    result = await dmp_mem_verify_extended_r(
        conn, address=0x100000, expected_data=b"\x01\x02\x03"
    )
    await responder

    assert result is None
    assert xknx.cemi_handler.send_telegram.call_args_list[0].args[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.MemoryExtendedRead(address=0x100000, count=3),
    )
    await conn.disconnect()


async def test_dmp_mem_verify_extended_r_mismatch(xknx_setup: XKNX) -> None:
    """Test dmp_mem_verify_extended_r raises VerificationError on a data mismatch."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(xknx, ia, seq=0, payload=_response(0x100000, b"\xff\x02\x03"))

    responder = asyncio.create_task(respond())
    with pytest.raises(VerificationError, match=r"expected 010203, got ff0203"):
        await dmp_mem_verify_extended_r(
            conn, address=0x100000, expected_data=b"\x01\x02\x03"
        )
    await responder

    await conn.disconnect()


async def test_dmp_mem_verify_extended_r_empty_expected_data(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_mem_verify_extended_r returns immediately for empty expected_data."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    result = await dmp_mem_verify_extended_r(conn, address=0x100000, expected_data=b"")

    assert result is None
    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dmp_mem_verify_extended_r_address_out_of_range(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_mem_verify_extended_r raises ValueError for an address outside 0-16777215."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"address must be 0-16777215, got 16777216"):
        await dmp_mem_verify_extended_r(conn, address=0x1000000, expected_data=b"\x01")
    await conn.disconnect()


async def test_dmp_mem_verify_extended_r_range_out_of_bounds(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_mem_verify_extended_r raises ValueError when the address range overflows 0xFFFFFF."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(
        ValueError, match=r"address \+ len\(expected_data\) - 1 must be <= 0xffffff"
    ):
        await dmp_mem_verify_extended_r(
            conn, address=0xFFFFFF, expected_data=b"\x01\x02"
        )
    await conn.disconnect()


async def test_dmp_mem_verify_extended_r_max_apdu_length_not_positive(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_mem_verify_extended_r raises ValueError for max_apdu_length <= 0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"max_apdu_length must be positive, got 0"):
        await dmp_mem_verify_extended_r(
            conn, address=0x100000, expected_data=b"\x01", max_apdu_length=0
        )
    await conn.disconnect()


async def test_dmp_mem_verify_extended_r_no_room_for_data(xknx_setup: XKNX) -> None:
    """Test dmp_mem_verify_extended_r raises ValueError when max_apdu_length leaves no room for data."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"leaves no room for memory data"):
        await dmp_mem_verify_extended_r(
            conn, address=0x100000, expected_data=b"\x01", max_apdu_length=5
        )
    await conn.disconnect()


async def test_dmp_mem_verify_extended_r_negative_return_code_raises(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_mem_verify_extended_r raises when the response carries a negative return code."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx, ia, seq=0, payload=_response(0x100000, b"", return_code=0xFD)
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"return code 0xfd"):
        await dmp_mem_verify_extended_r(
            conn, address=0x100000, expected_data=b"\x01\x02\x03"
        )
    await responder

    await conn.disconnect()


async def test_dmp_mem_verify_extended_r_error_short_response(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_mem_verify_extended_r raises when a chunk's response is shorter than requested."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(xknx, ia, seq=0, payload=_response(0x100000, b"\x01\x02"))

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"requested 3 octets, got 2"):
        await dmp_mem_verify_extended_r(
            conn, address=0x100000, expected_data=b"\x01\x02\x03"
        )
    await responder

    await conn.disconnect()


async def test_dmp_mem_verify_extended_r_wrong_address_echoed(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_mem_verify_extended_r raises when a response echoes a different address."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(xknx, ia, seq=0, payload=_response(0x200000, b"\x01\x02\x03"))

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"response echoed 0x200000"):
        await dmp_mem_verify_extended_r(
            conn, address=0x100000, expected_data=b"\x01\x02\x03"
        )
    await responder

    await conn.disconnect()
