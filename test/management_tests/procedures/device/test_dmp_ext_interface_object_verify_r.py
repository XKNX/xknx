"""Tests for dmp_ext_interface_object_verify_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.26.3."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError, PropertyVerificationError
from xknx.management.procedures import dmp_ext_interface_object_verify_r
from xknx.telegram import Telegram, apci

from ._ext_harness import IA, process_response, request, sent, wait_for_sent

EXPECTED = bytes.fromhex("11ef11ee11ed")


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
            property_id=53,
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
        property_id=53,
        nr_of_elem=count,
        start_index=start_index,
        data=data,
    )


async def test_verify_blocks(xknx_setup: XKNX) -> None:
    """Blocks are sized by max_apdu_length - 9 and each one is compared."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _response(2, 1, EXPECTED[:4]))
        await wait_for_sent(xknx, 3)
        process_response(xknx, 1, _response(1, 3, EXPECTED[4:]))

    responder = asyncio.create_task(respond())
    await dmp_ext_interface_object_verify_r(
        conn,
        object_type=11,
        object_instance=1,
        property_id=53,
        expected_data=EXPECTED,
        count=3,
        max_apdu_length=13,  # (13 - 9) // 2 == 2 elements per block
    )
    await responder
    assert sent(xknx)[::2] == [_read(0, 2, 1), _read(1, 1, 3)]
    await conn.disconnect()


async def test_verify_mismatch(xknx_setup: XKNX) -> None:
    """Different data raises PropertyVerificationError."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _response(1, 1, b"\xff\xff"))

    responder = asyncio.create_task(respond())
    with pytest.raises(PropertyVerificationError):
        await dmp_ext_interface_object_verify_r(
            conn,
            object_type=11,
            object_instance=1,
            property_id=53,
            expected_data=EXPECTED[:2],
        )
    await responder
    await conn.disconnect()


async def test_verify_error_response(xknx_setup: XKNX) -> None:
    """nr_of_elem=0 is a negative response."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _response(0, 1, b"\xf2"))

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="nr_of_elem=0"):
        await dmp_ext_interface_object_verify_r(
            conn,
            object_type=11,
            object_instance=1,
            property_id=53,
            expected_data=EXPECTED[:2],
        )
    await responder
    await conn.disconnect()


async def test_verify_partial_response(xknx_setup: XKNX) -> None:
    """A response with another element count than requested is an error."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _response(1, 1, EXPECTED[:2]))

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="requested 3 elements, got 1"):
        await dmp_ext_interface_object_verify_r(
            conn,
            object_type=11,
            object_instance=1,
            property_id=53,
            expected_data=EXPECTED,
            count=3,
        )
    await responder
    await conn.disconnect()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"count": 0}, "count must be positive"),
        ({"count": 4}, "must be divisible"),
        ({"start_index": 0}, "start_index must be >= 1"),
        ({"start_index": 0xFFFF, "count": 3}, "must be <= 65535"),
        ({"max_apdu_length": 0}, "max_apdu_length must be positive"),
    ],
)
async def test_verify_invalid_arguments(
    xknx_setup: XKNX, kwargs: dict[str, int], message: str
) -> None:
    """Invalid arguments are rejected before anything is sent."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()
    with pytest.raises(ValueError, match=message):
        await dmp_ext_interface_object_verify_r(
            conn,
            object_type=11,
            object_instance=1,
            property_id=53,
            expected_data=EXPECTED,
            **kwargs,
        )
    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()
