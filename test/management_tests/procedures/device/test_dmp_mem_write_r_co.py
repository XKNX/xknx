"""Tests for dmp_mem_write_r_co — KNX v02.01.02 - Management Procedures 03.05.02 - §3.16.2."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.procedures.device.dmp_mem_write_r_co import dmp_mem_write_r_co
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
    """
    Inject ACK (+ optional TDataConnected response) into the management layer.

    ``ack_seq`` is our own outgoing telegram's sequence number (echoed back by
    the device's ACK); ``response_seq`` is the device's own incoming sequence
    counter for data it sends us, which starts at 0 independently and only
    advances on an actual TDataConnected payload - not on every ACK.
    """
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


async def test_dmp_mem_write_r_co_no_verify(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_r_co writes without a read-back, waiting only for the ACK."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process_response(xknx, ia, ack_seq=0)

    responder = asyncio.create_task(respond())
    await dmp_mem_write_r_co(conn, address=0x1000, data=b"\x01\x02\x03")
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(
            Telegram(
                destination_address=ia,
                tpci=tpci.TDataConnected(0),
                payload=apci.MemoryWrite(address=0x1000, data=b"\x01\x02\x03"),
            )
        )
    ]
    await conn.disconnect()


async def test_dmp_mem_write_r_co_chunked(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_r_co splits a write exceeding the wire chunk size."""
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
    # default max_apdu_length=15 -> 15 - 3 (header) = 12 octets per chunk
    await dmp_mem_write_r_co(conn, address=0x1000, data=b"\x01" * 15)
    await responder

    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(0),
            payload=apci.MemoryWrite(address=0x1000, data=b"\x01" * 12),
        ),
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(1),
            payload=apci.MemoryWrite(address=0x100C, data=b"\x01" * 3),
        ),
    ]
    await conn.disconnect()


async def test_dmp_mem_write_r_co_verify_success(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_r_co with verify=True reads back and compares each chunk."""
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
            payload=apci.MemoryResponse(address=0x1000, data=b"\x01\x02\x03"),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    await dmp_mem_write_r_co(conn, address=0x1000, data=b"\x01\x02\x03", verify=True)
    await responder

    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(0),
            payload=apci.MemoryWrite(address=0x1000, data=b"\x01\x02\x03"),
        ),
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(1),
            payload=apci.MemoryRead(address=0x1000, count=3),
        ),
        # our ACK of the device's incoming MemoryResponse (response_seq=0)
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
    ]
    await conn.disconnect()


async def test_dmp_mem_write_r_co_verify_mismatch(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_r_co with verify=True raises VerificationError when the read-back differs."""
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
            payload=apci.MemoryResponse(address=0x1000, data=b"\xff\xff\xff"),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(VerificationError, match=r"Memory verify failed"):
        await dmp_mem_write_r_co(
            conn, address=0x1000, data=b"\x01\x02\x03", verify=True
        )
    await responder

    await conn.disconnect()


async def test_dmp_mem_write_r_co_verify_wrong_address_echoed(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_r_co with verify=True raises when the read-back echoes a different address."""
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
            payload=apci.MemoryResponse(address=0x2000, data=b"\x01\x02\x03"),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"response echoed 0x2000"):
        await dmp_mem_write_r_co(
            conn, address=0x1000, data=b"\x01\x02\x03", verify=True
        )
    await responder

    await conn.disconnect()


async def test_dmp_mem_write_r_co_range_out_of_bounds(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_r_co raises ValueError when address + len(data) - 1 overflows 0xFFFF."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(
        ValueError, match=r"address \+ len\(data\) - 1 must be <= 0xffff"
    ):
        await dmp_mem_write_r_co(conn, address=0xFFFF, data=b"\x01\x02")
    await conn.disconnect()


async def test_dmp_mem_write_r_co_empty_data(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_r_co is a no-op for empty data."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    await dmp_mem_write_r_co(conn, address=0x1000, data=b"")

    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dmp_mem_write_r_co_address_out_of_range(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_r_co raises ValueError for an address outside 0-65535."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"address must be 0-65535, got 65536"):
        await dmp_mem_write_r_co(conn, address=0x10000, data=b"\x01")
    await conn.disconnect()


async def test_dmp_mem_write_r_co_max_apdu_length_not_positive(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_mem_write_r_co raises ValueError for max_apdu_length <= 0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"max_apdu_length must be positive, got 0"):
        await dmp_mem_write_r_co(conn, address=0x1000, data=b"\x01", max_apdu_length=0)
    await conn.disconnect()


async def test_dmp_mem_write_r_co_no_room_for_data(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_r_co raises ValueError when max_apdu_length leaves no room for data."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"leaves no room for memory data"):
        await dmp_mem_write_r_co(conn, address=0x1000, data=b"\x01", max_apdu_length=3)
    await conn.disconnect()


async def test_dmp_mem_write_r_co_write_delay(xknx_setup: XKNX) -> None:
    """Test dmp_mem_write_r_co sleeps write_delay after each chunk when not verifying."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process_response(xknx, ia, ack_seq=0)

    responder = asyncio.create_task(respond())
    start = asyncio.get_running_loop().time()
    await dmp_mem_write_r_co(
        conn, address=0x1000, data=b"\x01\x02\x03", write_delay=0.05
    )
    elapsed = asyncio.get_running_loop().time() - start
    await responder

    assert elapsed >= 0.05
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(
            Telegram(
                destination_address=ia,
                tpci=tpci.TDataConnected(0),
                payload=apci.MemoryWrite(address=0x1000, data=b"\x01\x02\x03"),
            )
        )
    ]
    await conn.disconnect()
