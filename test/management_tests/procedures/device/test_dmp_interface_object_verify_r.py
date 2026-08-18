"""Tests for dmp_interface_object_verify_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.26.2 DMP_InterfaceObjectVerify_R."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError, PropertyVerificationError
from xknx.management.procedures.device.dmp_interface_object_verify_r import (
    dmp_interface_object_verify_r,
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


def _verify_request(
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


async def test_dmp_interface_object_verify_r_match(xknx_setup: XKNX) -> None:
    """Test verify passes when device data matches expected."""
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
                object_index=0, property_id=78, count=1, start_index=1, data=b"\xab\xcd"
            ),
        )

    responder = asyncio.create_task(respond())
    await dmp_interface_object_verify_r(
        conn, object_index=0, property_id=78, expected_data=b"\xab\xcd", count=1
    )
    await responder
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_mismatch(xknx_setup: XKNX) -> None:
    """Test verify raises PropertyVerificationError when data does not match."""
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
                object_index=0, property_id=78, count=1, start_index=1, data=b"\x00\x00"
            ),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(PropertyVerificationError, match="Property verify mismatch"):
        await dmp_interface_object_verify_r(
            conn, object_index=0, property_id=78, expected_data=b"\xab\xcd", count=1
        )
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
            xknx,
            ia,
            seq=0,
            payload=apci.PropertyValueResponse(
                object_index=0, property_id=78, count=0, start_index=1, data=b""
            ),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="nr_of_elem=0"):
        await dmp_interface_object_verify_r(
            conn, object_index=0, property_id=78, expected_data=b"\xab\xcd", count=1
        )
    await responder
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_max_apdu_length_not_positive(
    xknx_setup: XKNX,
) -> None:
    """Test dmp_interface_object_verify_r raises ValueError for max_apdu_length <= 0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)

    with pytest.raises(ValueError, match=r"max_apdu_length must be positive, got 0"):
        await dmp_interface_object_verify_r(
            conn,
            object_index=0,
            property_id=78,
            expected_data=b"\xab\xcd",
            count=1,
            max_apdu_length=0,
        )

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
    await dmp_interface_object_verify_r(
        conn,
        object_index=0,
        property_id=52,
        expected_data=expected,
        count=20,
        max_apdu_length=21,  # (21 - 6) // 1 == 15, matching the wire cap exactly
    )
    await responder

    # the second chunk must continue at start_index=16, not restart or overlap
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _verify_request(ia, 0, object_index=0, property_id=52, count=15, start_index=1),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _verify_request(ia, 1, object_index=0, property_id=52, count=5, start_index=16),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
    ]
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_chunked_mismatch_first_block(
    xknx_setup: XKNX,
) -> None:
    """Test chunked verify fails immediately on first-block mismatch without sending a second request."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    expected = b"\x01" * 15 + b"\x02" * 5

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
                data=b"\xff" * 15,
            ),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(PropertyVerificationError, match="Property verify mismatch"):
        await dmp_interface_object_verify_r(
            conn,
            object_index=0,
            property_id=52,
            expected_data=expected,
            count=20,
            max_apdu_length=21,  # (21 - 6) // 1 == 15, matching the wire cap exactly
        )
    await responder

    # only one request sent — early termination on first-block mismatch
    assert xknx.cemi_handler.send_telegram.call_count == 2  # request + ACK back
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_chunked_mismatch_second_block(
    xknx_setup: XKNX,
) -> None:
    """Test chunked verify passes first block then fails on second-block mismatch."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    expected = b"\x01" * 15 + b"\x02" * 5

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
                data=b"\xff" * 5,
            ),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(PropertyVerificationError, match="Property verify mismatch"):
        await dmp_interface_object_verify_r(
            conn,
            object_index=0,
            property_id=52,
            expected_data=expected,
            count=20,
            max_apdu_length=21,  # (21 - 6) // 1 == 15, matching the wire cap exactly
        )
    await responder
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_max_apdu_length(xknx_setup: XKNX) -> None:
    """Test max_apdu_length further limits chunk size below the 15-element cap."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    # element_size=4 (20 bytes / 5 elements); with max_apdu_length=14 only
    # (14 - 6) // 4 = 2 elements fit per request, well below the 15-element
    # wire cap, so this must split into three requests instead of one.
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
    await dmp_interface_object_verify_r(
        conn,
        object_index=0,
        property_id=60,
        expected_data=expected,
        count=5,
        start_index=1,
        max_apdu_length=14,
    )
    await responder

    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _verify_request(ia, 0, object_index=0, property_id=60, count=2, start_index=1),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _verify_request(ia, 1, object_index=0, property_id=60, count=2, start_index=3),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
        _verify_request(ia, 2, object_index=0, property_id=60, count=1, start_index=5),
        Telegram(destination_address=ia, tpci=tpci.TAck(2)),
    ]
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_count_zero(xknx_setup: XKNX) -> None:
    """Test verify with count=0 raises ValueError without sending a request."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    with pytest.raises(ValueError, match=r"count must be positive, got 0"):
        await dmp_interface_object_verify_r(
            conn, object_index=0, property_id=78, expected_data=b"\xab\xcd", count=0
        )

    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_start_index_zero(xknx_setup: XKNX) -> None:
    """Test verify with start_index=0 raises ValueError without sending a request."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    with pytest.raises(ValueError, match=r"start_index must be >= 1, got 0"):
        await dmp_interface_object_verify_r(
            conn,
            object_index=0,
            property_id=78,
            expected_data=b"\xab\xcd\xab\xcd",
            count=2,
            start_index=0,
        )

    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dmp_interface_object_verify_r_invalid_data_length(
    xknx_setup: XKNX,
) -> None:
    """Test verify raises ValueError when expected_data length is not divisible by count."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)

    with pytest.raises(ValueError, match=r"expected_data length .* must be divisible"):
        await dmp_interface_object_verify_r(
            conn,
            object_index=0,
            property_id=78,
            expected_data=b"\x01\x02\x03",
            count=2,
        )

    await conn.disconnect()


async def test_dmp_interface_object_verify_r_error_partial_response(
    xknx_setup: XKNX,
) -> None:
    """Test verify raises ManagementConnectionError on a partial response (not in spec, defensive)."""
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
        await dmp_interface_object_verify_r(
            conn,
            object_index=0,
            property_id=52,
            expected_data=b"\x01" * 5,
            count=5,
        )
    await responder
    await conn.disconnect()
