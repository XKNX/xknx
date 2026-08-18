"""Tests for dmp_interface_object_write_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.25.2."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError, PropertyVerificationError
from xknx.management.procedures.device.dmp_interface_object_write_r import (
    dmp_interface_object_write_r,
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


def _write_request(
    ia: IndividualAddress,
    seq: int,
    object_index: int,
    property_id: int,
    data: bytes,
    **kwargs: int,
) -> Telegram:
    """Build the outgoing PropertyValueWrite telegram for a given sequence number."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(seq),
        payload=apci.PropertyValueWrite(
            object_index=object_index, property_id=property_id, data=data, **kwargs
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


async def test_dmp_interface_object_write_r_basic(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_write_r writes property value."""
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
    result = await dmp_interface_object_write_r(
        conn, object_index=0, property_id=78, data=b"\x00\x91", count=1, start_index=1
    )
    await responder

    assert result == b"\x00\x91"
    assert xknx.cemi_handler.send_telegram.call_args_list[0] == call(
        _write_request(
            ia,
            0,
            object_index=0,
            property_id=78,
            data=b"\x00\x91",
            count=1,
            start_index=1,
        )
    )
    await conn.disconnect()


async def test_dmp_interface_object_write_r_with_verify(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_write_r with verify enabled."""
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
                data=b"\xaa\xbb",
            ),
        )

    responder = asyncio.create_task(respond())
    result = await dmp_interface_object_write_r(
        conn,
        object_index=0,
        property_id=78,
        data=b"\xaa\xbb",
        count=1,
        start_index=1,
        verify=True,
    )
    await responder

    assert result == b"\xaa\xbb"
    await conn.disconnect()


async def test_dmp_interface_object_write_r_verify_failure(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_write_r raises PropertyVerificationError when verify fails."""
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
                data=b"\xff\xff",
            ),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(PropertyVerificationError, match="Property verify mismatch"):
        await dmp_interface_object_write_r(
            conn,
            object_index=0,
            property_id=78,
            data=b"\xaa\xbb",
            count=1,
            start_index=1,
            verify=True,
        )
    await responder

    await conn.disconnect()


async def test_dmp_interface_object_write_r_empty(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_write_r with empty data returns empty bytes."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    result = await dmp_interface_object_write_r(
        conn, object_index=0, property_id=78, data=b"", count=1
    )

    assert result == b""
    await conn.disconnect()


async def test_dmp_interface_object_write_r_count_zero(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_write_r raises ValueError for count=0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"count must be positive, got 0"):
        await dmp_interface_object_write_r(
            conn, object_index=0, property_id=78, data=b"\xaa\xbb", count=0
        )

    await conn.disconnect()


async def test_dmp_interface_object_write_r_invalid_data_length(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_interface_object_write_r raises ValueError for invalid data length."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"Data length .* must be divisible"):
        await dmp_interface_object_write_r(
            conn, object_index=0, property_id=78, data=b"\x01\x02\x03", count=2
        )

    await conn.disconnect()


async def test_dmp_interface_object_write_r_max_apdu_length_not_positive(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_interface_object_write_r raises ValueError for max_apdu_length <= 0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"max_apdu_length must be positive, got 0"):
        await dmp_interface_object_write_r(
            conn, object_index=0, property_id=78, data=b"\xaa\xbb", count=1, max_apdu_length=0
        )

    await conn.disconnect()


async def test_dmp_interface_object_write_r_chunked(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_write_r with count > 15 uses multiple requests."""
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
    result = await dmp_interface_object_write_r(
        conn,
        object_index=0,
        property_id=52,
        data=b"\x01" * 15 + b"\x02" * 5,
        count=20,
        start_index=1,
        max_apdu_length=21,  # (21 - 6) // 1 == 15, matching the wire cap exactly
    )
    await responder

    assert result == b"\x01" * 15 + b"\x02" * 5
    # the second chunk must continue at start_index=16 with its own slice of
    # data, not restart, overlap, or resend the first chunk's bytes
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _write_request(
            ia,
            0,
            object_index=0,
            property_id=52,
            data=b"\x01" * 15,
            count=15,
            start_index=1,
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _write_request(
            ia,
            1,
            object_index=0,
            property_id=52,
            data=b"\x02" * 5,
            count=5,
            start_index=16,
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
    ]
    await conn.disconnect()


async def test_dmp_interface_object_write_r_default_max_apdu_length_budget(
    xknx_setup: XKNX,
) -> None:
    """Test the default max_apdu_length=15 budget yields exactly 10 elements/chunk for 1-byte elements.

    Pins PROPERTY_VALUE_HEADER_OCTETS=5: budget = 15 - 5 = 10, matching
    apci.PropertyValueWrite(data=b"").calculated_length() == 5 and Calimero's
    equivalent (maxApduLength - 1 - 4) == 10 for the same default of 15.
    """
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    data = bytes(range(11))

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx,
            ia,
            seq=0,
            payload=apci.PropertyValueResponse(
                object_index=0, property_id=52, count=10, start_index=1, data=data[0:10]
            ),
        )
        await _wait_for_request(xknx, 2)
        _process_response(
            xknx,
            ia,
            seq=1,
            payload=apci.PropertyValueResponse(
                object_index=0, property_id=52, count=1, start_index=11, data=data[10:11]
            ),
        )

    responder = asyncio.create_task(respond())
    result = await dmp_interface_object_write_r(
        conn, object_index=0, property_id=52, data=data, count=11, start_index=1
    )
    await responder

    assert result == data
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _write_request(
            ia, 0, object_index=0, property_id=52, data=data[0:10], count=10, start_index=1
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _write_request(
            ia, 1, object_index=0, property_id=52, data=data[10:11], count=1, start_index=11
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
    ]
    await conn.disconnect()


async def test_dmp_interface_object_write_r_max_apdu_length(xknx_setup: XKNX) -> None:
    """Test max_apdu_length further limits chunk size below the 15-element cap."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    # element_size=4 (20 bytes / 5 elements); with max_apdu_length=14 only
    # (14 - 6) // 4 = 2 elements fit per request, well below the 15-element
    # wire cap, so this must split into three requests instead of one.
    data = bytes(range(20))

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
                data=data[0:8],
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
                data=data[8:16],
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
                data=data[16:20],
            ),
        )

    responder = asyncio.create_task(respond())
    result = await dmp_interface_object_write_r(
        conn,
        object_index=0,
        property_id=60,
        data=data,
        count=5,
        start_index=1,
        max_apdu_length=14,
    )
    await responder

    assert result == data
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _write_request(
            ia, 0, object_index=0, property_id=60, data=data[0:8], count=2, start_index=1
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _write_request(
            ia, 1, object_index=0, property_id=60, data=data[8:16], count=2, start_index=3
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
        _write_request(
            ia, 2, object_index=0, property_id=60, data=data[16:20], count=1, start_index=5
        ),
        Telegram(destination_address=ia, tpci=tpci.TAck(2)),
    ]
    await conn.disconnect()


async def test_dmp_interface_object_write_r_error_partial_response(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_interface_object_write_r raises error on partial response (not in spec, defensive)."""
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
        await dmp_interface_object_write_r(
            conn,
            object_index=0,
            property_id=52,
            data=b"\x01\x02\x03\x04\x05",
            count=5,
            start_index=1,
        )
    await responder

    await conn.disconnect()


async def test_dmp_interface_object_write_r_error_nr_of_elem_zero(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_interface_object_write_r raises error when device returns nr_of_elem=0."""
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
        await dmp_interface_object_write_r(
            conn,
            object_index=0,
            property_id=78,
            data=b"\xaa\xbb",
            count=1,
            start_index=1,
        )
    await responder

    await conn.disconnect()
