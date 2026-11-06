"""Tests for dmp_ext_interface_object_read_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.27.4."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures import dmp_ext_interface_object_read_r
from xknx.telegram import Telegram, apci

from ._ext_harness import IA, ack, process_response, request, sent, wait_for_sent


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _read(seq: int, count: int, start_index: int) -> Telegram:
    return request(
        seq,
        apci.PropertyExtValueRead(
            interface_object_type=11,
            object_instance=1,
            property_id=201,
            nr_of_elem=count,
            start_index=start_index,
        ),
    )


def _response(
    count: int, start_index: int, data: bytes
) -> apci.PropertyExtValueResponse:
    return apci.PropertyExtValueResponse(
        interface_object_type=11,
        object_instance=1,
        property_id=201,
        nr_of_elem=count,
        start_index=start_index,
        data=data,
    )


async def test_read_single_element(xknx_setup: XKNX) -> None:
    """A single element is read with one A_PropertyExtValue_Read."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _response(1, 1, b"\x00\x2a"))

    responder = asyncio.create_task(respond())
    data = await dmp_ext_interface_object_read_r(
        conn, object_type=11, object_instance=1, property_id=201
    )
    await responder

    assert data == b"\x00\x2a"
    assert sent(xknx) == [_read(0, 1, 1), ack(0)]
    await conn.disconnect()


async def test_read_chunked_after_probe(xknx_setup: XKNX) -> None:
    """After the 1-element probe, blocks are sized by max_apdu_length - 9."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _response(1, 1, b"\x01\x01"))
        await wait_for_sent(xknx, 3)
        process_response(xknx, 1, _response(3, 2, b"\x02\x02" * 3))
        await wait_for_sent(xknx, 5)
        process_response(xknx, 2, _response(1, 5, b"\x03\x03"))

    responder = asyncio.create_task(respond())
    data = await dmp_ext_interface_object_read_r(
        conn,
        object_type=11,
        object_instance=1,
        property_id=201,
        count=5,
        max_apdu_length=15,  # (15 - 9) // 2 == 3 elements per block
    )
    await responder

    assert data == b"\x01\x01" + b"\x02\x02" * 3 + b"\x03\x03"
    assert sent(xknx)[::2] == [_read(0, 1, 1), _read(1, 3, 2), _read(2, 1, 5)]
    await conn.disconnect()


async def test_read_more_than_15_elements_per_block(xknx_setup: XKNX) -> None:
    """nr_of_elem is a full octet, so a block may carry more than 15 elements."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _response(1, 1, b"\x00"))
        await wait_for_sent(xknx, 3)
        process_response(xknx, 1, _response(20, 2, b"\x01" * 20))

    responder = asyncio.create_task(respond())
    data = await dmp_ext_interface_object_read_r(
        conn,
        object_type=11,
        object_instance=1,
        property_id=201,
        count=21,
        max_apdu_length=50,
    )
    await responder

    assert data == b"\x00" + b"\x01" * 20
    assert sent(xknx)[2] == _read(1, 20, 2)
    await conn.disconnect()


async def test_read_error_response(xknx_setup: XKNX) -> None:
    """nr_of_elem=0 is a negative response."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _response(0, 1, b"\xf2"))

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="nr_of_elem=0"):
        await dmp_ext_interface_object_read_r(
            conn, object_type=11, object_instance=1, property_id=201
        )
    await responder
    await conn.disconnect()


async def test_read_partial_response(xknx_setup: XKNX) -> None:
    """A response with another element count than requested is an error."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _response(1, 1, b"\x01"))
        await wait_for_sent(xknx, 3)
        process_response(xknx, 1, _response(2, 2, b"\x01\x01"))

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="requested 3 elements, got 2"):
        await dmp_ext_interface_object_read_r(
            conn, object_type=11, object_instance=1, property_id=201, count=4
        )
    await responder
    await conn.disconnect()


async def test_read_empty_probe(xknx_setup: XKNX) -> None:
    """A probe answered without data leaves the element size unknown."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _response(1, 1, b""))

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="empty data"):
        await dmp_ext_interface_object_read_r(
            conn, object_type=11, object_instance=1, property_id=201, count=2
        )
    await responder
    await conn.disconnect()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"count": 0}, "count must be positive"),
        ({"start_index": -1}, "start_index must be >= 0"),
        ({"start_index": 0, "count": 2}, "requires count=1"),
        ({"start_index": 0xFFFF, "count": 2}, "must be <= 65535"),
        ({"max_apdu_length": 0}, "max_apdu_length must be positive"),
    ],
)
async def test_read_invalid_arguments(
    xknx_setup: XKNX, kwargs: dict[str, int], message: str
) -> None:
    """Invalid arguments are rejected before anything is sent."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()
    with pytest.raises(ValueError, match=message):
        await dmp_ext_interface_object_read_r(
            conn, object_type=11, object_instance=1, property_id=201, **kwargs
        )
    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()
