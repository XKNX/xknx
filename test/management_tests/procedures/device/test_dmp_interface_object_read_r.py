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
    """Test dmp_interface_object_read_r with count > 1: 1-element probe, then the rest."""
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
                count=1,
                start_index=1,
                data=b"\x01\x02",
            ),
        )
        await _wait_for_request(xknx, 2)
        _process_response(
            xknx,
            ia,
            seq=1,
            payload=apci.PropertyValueResponse(
                object_index=1,
                property_id=52,
                count=2,
                start_index=2,
                data=b"\x03\x04\x05\x06",
            ),
        )

    responder = asyncio.create_task(respond())
    data = await dmp_interface_object_read_r(
        conn, object_index=1, property_id=52, count=3, start_index=1
    )
    await responder

    assert data == b"\x01\x02\x03\x04\x05\x06"
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _read_request(ia, 0, object_index=1, property_id=52, count=1, start_index=1),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _read_request(ia, 1, object_index=1, property_id=52, count=2, start_index=2),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
    ]
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


async def test_dmp_interface_object_read_r_start_index_overflow(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_interface_object_read_r raises ValueError when start_index + count - 1 > 4095."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(
        ValueError, match=r"start_index \+ count - 1 must be <= 4095, got 4096"
    ):
        await dmp_interface_object_read_r(
            conn, object_index=0, property_id=78, count=2, start_index=4095
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
    """Test dmp_interface_object_read_r with count > 15: probe, then 15-element wire-capped chunks."""
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
                count=1,
                start_index=1,
                data=b"\x01",
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
                count=15,
                start_index=2,
                data=b"\x01" * 15,
            ),
        )
        await _wait_for_request(xknx, 3)
        _process_response(
            xknx,
            ia,
            seq=2,
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=52,
                count=4,
                start_index=17,
                data=b"\x02" * 4,
            ),
        )

    responder = asyncio.create_task(respond())
    data = await dmp_interface_object_read_r(
        conn,
        object_index=0,
        property_id=52,
        count=20,
        start_index=1,
        max_apdu_length=21,  # (21 - 5) // 1 == 16, min'd with the 15-element wire cap
    )
    await responder

    assert data == b"\x01" * 16 + b"\x02" * 4
    # each chunk must continue where the previous left off, not restart or overlap
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _read_request(ia, 0, object_index=0, property_id=52, count=1, start_index=1),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _read_request(ia, 1, object_index=0, property_id=52, count=15, start_index=2),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
        _read_request(ia, 2, object_index=0, property_id=52, count=4, start_index=17),
        Telegram(destination_address=ia, tpci=tpci.TAck(2)),
    ]
    await conn.disconnect()


async def test_dmp_interface_object_read_r_max_apdu_length(xknx_setup: XKNX) -> None:
    """
    Test element_size discovered from the probe tightens later chunks' size.

    element_size=4 is only known after the 1-element probe response; with
    max_apdu_length=14, (14 - 5) // 4 == 2 elements/chunk for everything
    after that.
    """
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    expected = bytes(range(20))  # 5 elements * 4 bytes

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx,
            ia,
            seq=0,
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=60,
                count=1,
                start_index=1,
                data=expected[0:4],
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
                start_index=2,
                data=expected[4:12],
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
                count=2,
                start_index=4,
                data=expected[12:20],
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
    )
    await responder

    assert data == expected
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _read_request(ia, 0, object_index=0, property_id=60, count=1, start_index=1),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _read_request(ia, 1, object_index=0, property_id=60, count=2, start_index=2),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
        _read_request(ia, 2, object_index=0, property_id=60, count=2, start_index=4),
        Telegram(destination_address=ia, tpci=tpci.TAck(2)),
    ]
    await conn.disconnect()


async def test_dmp_interface_object_read_r_error_partial_response(
    xknx_setup: XKNX,
) -> None:
    """
    Test dmp_interface_object_read_r raises error when a response's count doesn't match the request.

    The 1-element probe itself is the mismatched response here (not in spec,
    defensive).
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
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=52,
                count=2,  # probe requested 1, got 2
                start_index=1,
                data=b"\x01\x02",
            ),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"requested 1 elements, got 2"):
        await dmp_interface_object_read_r(
            conn, object_index=0, property_id=52, count=5, start_index=1
        )
    await responder

    await conn.disconnect()


async def test_dmp_interface_object_read_r_error_partial_response_after_probe(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_interface_object_read_r raises error when a post-probe chunk's count mismatches."""
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
                object_index=0, property_id=52, count=1, start_index=1, data=b"\x01"
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
                count=2,  # requested 4, got 2
                start_index=2,
                data=b"\x02\x03",
            ),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"requested 4 elements, got 2"):
        await dmp_interface_object_read_r(
            conn, object_index=0, property_id=52, count=5, start_index=1
        )
    await responder

    await conn.disconnect()


async def test_dmp_interface_object_read_r_error_empty_probe_data(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_interface_object_read_r raises error when the probe response has empty data."""
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
                object_index=0, property_id=52, count=1, start_index=1, data=b""
            ),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(
        ManagementConnectionError, match=r"returned empty data for 1 element"
    ):
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
