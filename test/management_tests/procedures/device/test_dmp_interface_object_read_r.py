"""Tests for dmp_interface_object_read_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.27.2."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_interface_object_read_r import (
    dmp_interface_object_read_r,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci
from xknx.util import asyncio_timeout

RESPONDER_TIMEOUT = 1


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _read_request(
    ia: IndividualAddress, seq: int, object_index: int, property_id: int, **kwargs: int
) -> Telegram:
    """Build the outgoing PropertyValueRead telegram for a given sequence number."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(seq),
        payload=apci.PropertyValueRead(
            object_index=object_index, property_id=property_id, **kwargs
        ),
    )


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
    async with asyncio_timeout(RESPONDER_TIMEOUT):
        while xknx.cemi_handler.send_telegram.call_count < threshold:  # noqa: ASYNC110
            await asyncio.sleep(0)


async def test_dmp_interface_object_read_r_basic(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_read_r reads property value."""
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
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=78,
                count=1,
                start_index=1,
                data=b"\x00\x91",
            ),
        )

    responder = asyncio.create_task(respond())
    data = await dmp_interface_object_read_r(
        conn, object_index=0, property_id=78, count=1, start_index=1
    )
    await responder

    assert data == b"\x00\x91"
    assert xknx.cemi_handler.send_telegram.call_args_list[0] == call(
        _read_request(ia, 0, object_index=0, property_id=78, count=1, start_index=1)
    )
    await conn.disconnect()


async def test_dmp_interface_object_read_r_multiple_elements(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_read_r with count > 1."""
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
            payload=apci.PropertyValueResponse(
                object_index=1,
                property_id=52,
                count=3,
                start_index=1,
                data=b"\x01\x02\x03\x04\x05\x06",
            ),
        )

    responder = asyncio.create_task(respond())
    data = await dmp_interface_object_read_r(
        conn, object_index=1, property_id=52, count=3, start_index=1
    )
    await responder

    assert data == b"\x01\x02\x03\x04\x05\x06"
    await conn.disconnect()


async def test_dmp_interface_object_read_r_count_zero(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_read_r raises ValueError for count=0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"count must be positive, got 0"):
        await dmp_interface_object_read_r(conn, object_index=0, property_id=78, count=0)

    await conn.disconnect()


async def test_dmp_interface_object_read_r_start_index_zero(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_read_r raises ValueError for start_index=0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"start_index must be >= 1, got 0"):
        await dmp_interface_object_read_r(
            conn, object_index=0, property_id=78, count=2, start_index=0
        )

    await conn.disconnect()


async def test_dmp_interface_object_read_r_max_apdu_length_not_positive(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_interface_object_read_r raises ValueError for max_apdu_length <= 0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"max_apdu_length must be positive, got 0"):
        await dmp_interface_object_read_r(
            conn, object_index=0, property_id=78, count=1, max_apdu_length=0
        )

    await conn.disconnect()


async def test_dmp_interface_object_read_r_chunked(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_read_r with count > 15 uses multiple requests."""
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
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=52,
                count=15,
                start_index=1,
                data=b"\x01" * 15,
            ),
        )
        await _wait_for_request(xknx, 2)
        _process_response(
            xknx,
            ia,
            seq=1,
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=52,
                count=5,
                start_index=16,
                data=b"\x02" * 5,
            ),
        )

    responder = asyncio.create_task(respond())
    data = await dmp_interface_object_read_r(
        conn,
        object_index=0,
        property_id=52,
        count=20,
        start_index=1,
        max_apdu_length=21,  # (21 - 6) // 1 == 15, matching the wire cap exactly
    )
    await responder

    assert data == b"\x01" * 15 + b"\x02" * 5
    # the second chunk must continue at start_index=16, not restart or overlap
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _read_request(ia, 0, object_index=0, property_id=52, count=15, start_index=1),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _read_request(ia, 1, object_index=0, property_id=52, count=5, start_index=16),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
    ]
    await conn.disconnect()


async def test_dmp_interface_object_read_r_max_apdu_length(xknx_setup: XKNX) -> None:
    """Test max_apdu_length + element_size further limits chunk size below the 15-element cap."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    # element_size=4; with max_apdu_length=14 only (14 - 6) // 4 = 2 elements
    # fit per request, well below the 15-element wire cap, so this must split
    # into three requests instead of one.
    expected = bytes(range(20))

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx,
            ia,
            seq=0,
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=60,
                count=2,
                start_index=1,
                data=expected[0:8],
            ),
        )
        await _wait_for_request(xknx, 2)
        _process_response(
            xknx,
            ia,
            seq=1,
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=60,
                count=2,
                start_index=3,
                data=expected[8:16],
            ),
        )
        await _wait_for_request(xknx, 3)
        _process_response(
            xknx,
            ia,
            seq=2,
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=60,
                count=1,
                start_index=5,
                data=expected[16:20],
            ),
        )

    responder = asyncio.create_task(respond())
    data = await dmp_interface_object_read_r(
        conn,
        object_index=0,
        property_id=60,
        count=5,
        start_index=1,
        max_apdu_length=14,
        element_size=4,
    )
    await responder

    assert data == expected
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _read_request(ia, 0, object_index=0, property_id=60, count=2, start_index=1),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _read_request(ia, 1, object_index=0, property_id=60, count=2, start_index=3),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
        _read_request(ia, 2, object_index=0, property_id=60, count=1, start_index=5),
        Telegram(destination_address=ia, tpci=tpci.TAck(2)),
    ]
    await conn.disconnect()


async def test_dmp_interface_object_read_r_error_partial_response(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_interface_object_read_r raises error on partial response (not in spec, defensive)."""
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
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=52,
                count=2,  # requested 5, got 2
                start_index=1,
                data=b"\x01\x02",
            ),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"requested 5 elements, got 2"):
        await dmp_interface_object_read_r(
            conn, object_index=0, property_id=52, count=5, start_index=1
        )
    await responder

    await conn.disconnect()


async def test_dmp_interface_object_read_r_error_nr_of_elem_zero(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_interface_object_read_r raises error when device returns nr_of_elem=0."""
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
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=78,
                count=0,
                start_index=1,
                data=b"",
            ),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"nr_of_elem=0"):
        await dmp_interface_object_read_r(
            conn, object_index=0, property_id=78, count=1, start_index=1
        )
    await responder

    await conn.disconnect()
