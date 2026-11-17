"""Tests for dmp_ext_interface_object_write_con_r/_uncon_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.25.4/§3.25.5."""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures import (
    dmp_ext_interface_object_write_con_r,
    dmp_ext_interface_object_write_uncon_r,
)
from xknx.telegram import Telegram, apci

from ._ext_harness import (
    IA,
    ack,
    process_ack,
    process_response,
    request,
    sent,
    wait_for_sent,
)

NAME = b"OpenKNX: IP-Interface (Dev)".ljust(30, b"\x00")


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _write_con(seq: int, count: int, start_index: int, data: bytes) -> Telegram:
    return request(
        seq,
        apci.PropertyExtValueWriteCon(
            interface_object_type=11,
            object_instance=1,
            property_id=76,
            nr_of_elem=count,
            start_index=start_index,
            data=data,
        ),
    )


def _write_uncon(seq: int, count: int, start_index: int, data: bytes) -> Telegram:
    return request(
        seq,
        apci.PropertyExtValueWriteUnCon(
            interface_object_type=11,
            object_instance=1,
            property_id=76,
            nr_of_elem=count,
            start_index=start_index,
            data=data,
        ),
    )


def _result(
    count: int,
    start_index: int,
    return_code: apci.ReturnCode = apci.ReturnCode.E_SUCCESS,
) -> apci.PropertyExtValueWriteConRes:
    return apci.PropertyExtValueWriteConRes(
        interface_object_type=11,
        object_instance=1,
        property_id=76,
        return_code=return_code,
        nr_of_elem=count,
        start_index=start_index,
    )


async def test_write_con_single_block(xknx_setup: XKNX) -> None:
    """A write that fits max_apdu_length is sent as one confirmed block."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _result(30, 1))

    responder = asyncio.create_task(respond())
    await dmp_ext_interface_object_write_con_r(
        conn,
        object_type=11,
        object_instance=1,
        property_id=76,
        data=NAME,
        count=30,
        max_apdu_length=50,
    )
    await responder

    assert sent(xknx) == [_write_con(0, 30, 1, NAME), ack(0)]
    await conn.disconnect()


async def test_write_con_chunked(xknx_setup: XKNX) -> None:
    """Blocks are sized by max_apdu_length - 9 and continue where the last ended."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _result(6, 1))
        await wait_for_sent(xknx, 3)
        process_response(xknx, 1, _result(4, 7))

    responder = asyncio.create_task(respond())
    await dmp_ext_interface_object_write_con_r(
        conn,
        object_type=11,
        object_instance=1,
        property_id=76,
        data=NAME[:10],
        count=10,
    )
    await responder

    assert sent(xknx)[::2] == [
        _write_con(0, 6, 1, NAME[:6]),
        _write_con(1, 4, 7, NAME[6:10]),
    ]
    await conn.disconnect()


async def test_write_con_return_code(xknx_setup: XKNX) -> None:
    """A return code other than E_SUCCESS fails the write."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _result(0, 1, apci.ReturnCode.E_ACCESS_DENIED))

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="E_ACCESS_DENIED"):
        await dmp_ext_interface_object_write_con_r(
            conn, object_type=11, object_instance=1, property_id=76, data=b"\x04"
        )
    await responder
    await conn.disconnect()


async def test_write_con_unexpected_confirmation(xknx_setup: XKNX) -> None:
    """A confirmation of another block fails the write."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_response(xknx, 0, _result(1, 2))

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="confirmed 1 at index 2"):
        await dmp_ext_interface_object_write_con_r(
            conn, object_type=11, object_instance=1, property_id=76, data=b"\x04"
        )
    await responder
    await conn.disconnect()


async def test_write_empty_data(xknx_setup: XKNX) -> None:
    """Nothing is sent for empty data."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()
    await dmp_ext_interface_object_write_con_r(
        conn, object_type=11, object_instance=1, property_id=76, data=b""
    )
    await dmp_ext_interface_object_write_uncon_r(
        conn, object_type=11, object_instance=1, property_id=76, data=b""
    )
    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_write_uncon_chunked(xknx_setup: XKNX) -> None:
    """Unconfirmed blocks only wait for the transport layer ACK."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await wait_for_sent(xknx, 1)
        process_ack(xknx, 0)
        await wait_for_sent(xknx, 2)
        process_ack(xknx, 1)

    responder = asyncio.create_task(respond())
    await dmp_ext_interface_object_write_uncon_r(
        conn,
        object_type=11,
        object_instance=1,
        property_id=76,
        data=NAME[:10],
        count=10,
    )
    await responder

    assert sent(xknx) == [
        _write_uncon(0, 6, 1, NAME[:6]),
        _write_uncon(1, 4, 7, NAME[6:10]),
    ]
    await conn.disconnect()


@pytest.mark.parametrize(
    "procedure",
    [dmp_ext_interface_object_write_con_r, dmp_ext_interface_object_write_uncon_r],
)
@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"count": 0}, "count must be positive"),
        ({"count": 3}, "must be divisible"),
        ({"start_index": -1}, "start_index must be >= 0"),
        ({"start_index": 0xFFFF, "count": 2}, "must be <= 65535"),
        ({"max_apdu_length": 0}, "max_apdu_length must be positive"),
    ],
)
async def test_write_invalid_arguments(
    xknx_setup: XKNX,
    procedure: Callable[..., Awaitable[None]],
    kwargs: dict[str, Any],
    message: str,
) -> None:
    """Invalid arguments are rejected before anything is sent."""
    xknx = xknx_setup
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()
    with pytest.raises(ValueError, match=message):
        await procedure(
            conn,
            object_type=11,
            object_instance=1,
            property_id=76,
            data=b"\x01\x02\x03\x04",
            **kwargs,
        )
    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()
