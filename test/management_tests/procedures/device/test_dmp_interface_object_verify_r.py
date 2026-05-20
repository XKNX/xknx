"""Tests for dmp_interface_object_verify_r — KNX 03.05.02 §3.26.2 DMP_InterfaceObjectVerify_R."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_interface_object_verify_r import (
    dmp_interface_object_verify_r,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


@pytest.fixture
def xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _process_response(
    xknx: XKNX,
    ia: IndividualAddress,
    seq: int,
    payload: apci.APCI,
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
    while xknx.cemi_handler.send_telegram.call_count < threshold:  # noqa: ASYNC110
        await asyncio.sleep(0)


async def test_dmp_interface_object_verify_r_match(xknx_setup: XKNX) -> None:
    """Test verify passes when device data matches expected."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx, ia, seq=0,
            payload=apci.PropertyValueResponse(object_index=0, property_id=78, count=1, start_index=1, data=b"\xAB\xCD"),
        )

    responder = asyncio.create_task(respond())
    await dmp_interface_object_verify_r(conn, object_index=0, property_id=78, expected_data=b"\xAB\xCD", count=1)
    await responder
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_mismatch(xknx_setup: XKNX) -> None:
    """Test verify raises ManagementConnectionError when data does not match."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx, ia, seq=0,
            payload=apci.PropertyValueResponse(object_index=0, property_id=78, count=1, start_index=1, data=b"\x00\x00"),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="Property verify failed"):
        await dmp_interface_object_verify_r(conn, object_index=0, property_id=78, expected_data=b"\xAB\xCD", count=1)
    await responder
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_read_error(xknx_setup: XKNX) -> None:
    """Test verify raises ManagementConnectionError when device returns nr_of_elem=0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx, ia, seq=0,
            payload=apci.PropertyValueResponse(object_index=0, property_id=78, count=0, start_index=1, data=b""),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="nr_of_elem=0"):
        await dmp_interface_object_verify_r(conn, object_index=0, property_id=78, expected_data=b"\xAB\xCD", count=1)
    await responder
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_chunked_match(xknx_setup: XKNX) -> None:
    """Test verify with count > 15 reads and compares in two blocks."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    expected = b"\x01" * 15 + b"\x02" * 5

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx, ia, seq=0,
            payload=apci.PropertyValueResponse(object_index=0, property_id=52, count=15, start_index=1, data=b"\x01" * 15),
        )
        await _wait_for_request(xknx, 2)
        _process_response(
            xknx, ia, seq=1,
            payload=apci.PropertyValueResponse(object_index=0, property_id=52, count=5, start_index=16, data=b"\x02" * 5),
        )

    responder = asyncio.create_task(respond())
    await dmp_interface_object_verify_r(conn, object_index=0, property_id=52, expected_data=expected, count=20)
    await responder
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_chunked_mismatch_first_block(xknx_setup: XKNX) -> None:
    """Test chunked verify fails immediately on first-block mismatch without sending a second request."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    expected = b"\x01" * 15 + b"\x02" * 5

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx, ia, seq=0,
            payload=apci.PropertyValueResponse(object_index=0, property_id=52, count=15, start_index=1, data=b"\xFF" * 15),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="Property verify failed"):
        await dmp_interface_object_verify_r(conn, object_index=0, property_id=52, expected_data=expected, count=20)
    await responder

    # only one request sent — early termination on first-block mismatch
    assert xknx.cemi_handler.send_telegram.call_count == 2  # request + ACK back
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_chunked_mismatch_second_block(xknx_setup: XKNX) -> None:
    """Test chunked verify passes first block then fails on second-block mismatch."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    expected = b"\x01" * 15 + b"\x02" * 5

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx, ia, seq=0,
            payload=apci.PropertyValueResponse(object_index=0, property_id=52, count=15, start_index=1, data=b"\x01" * 15),
        )
        await _wait_for_request(xknx, 2)
        _process_response(
            xknx, ia, seq=1,
            payload=apci.PropertyValueResponse(object_index=0, property_id=52, count=5, start_index=16, data=b"\xFF" * 5),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="Property verify failed"):
        await dmp_interface_object_verify_r(conn, object_index=0, property_id=52, expected_data=expected, count=20)
    await responder
    await conn.disconnect()
