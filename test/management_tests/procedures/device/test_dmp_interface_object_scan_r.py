"""Tests for dmp_interface_object_scan_r — KNX 03.05.02 §3.28.2 DMP_InterfaceObjectScan_R."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_interface_object_scan_r import (
    ScannedInterfaceObject,
    dmp_interface_object_scan_r,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _prop_desc(
    xknx: XKNX,
    ia: IndividualAddress,
    seq: int,
    object_index: int,
    property_id: int,
    property_index: int = 0,
) -> None:
    """Inject a PropertyDescriptionResponse into the management layer."""
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
            payload=apci.PropertyDescriptionResponse(
                object_index=object_index,
                property_id=property_id,
                property_index=property_index,
            ),
        )
    )


def _prop_val(
    xknx: XKNX,
    ia: IndividualAddress,
    seq: int,
    object_index: int,
    property_id: int,
    data: bytes,
) -> None:
    """Inject a PropertyValueResponse into the management layer."""
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
            payload=apci.PropertyValueResponse(
                object_index=object_index,
                property_id=property_id,
                count=1,
                start_index=1,
                data=data,
            ),
        )
    )


async def _wait_for_request(xknx: XKNX, req_num: int) -> None:
    """Wait until the req_num-th request telegram has been sent (1-indexed)."""
    threshold = req_num * 2 - 1
    while xknx.cemi_handler.send_telegram.call_count < threshold:  # noqa: ASYNC110
        await asyncio.sleep(0)


async def test_dmp_interface_object_scan_r_no_objects(xknx_setup: XKNX) -> None:
    """Test scan returns empty list when first object does not exist (PID=0)."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _prop_desc(xknx, ia, seq=0, object_index=0, property_id=0)

    responder = asyncio.create_task(respond())
    result = await dmp_interface_object_scan_r(conn)
    await responder

    assert result == []
    await conn.disconnect()


async def test_dmp_interface_object_scan_r_single_object_single_property(xknx_setup: XKNX) -> None:
    """Test scan discovers one object with exactly one property."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _prop_desc(xknx, ia, seq=0, object_index=0, property_id=1, property_index=0)  # outer: exists
        await _wait_for_request(xknx, 2)
        _prop_val(xknx, ia, seq=1, object_index=0, property_id=1, data=b"\x00\x01")   # type read
        await _wait_for_request(xknx, 3)
        _prop_desc(xknx, ia, seq=2, object_index=0, property_id=78, property_index=0) # inner idx=0
        await _wait_for_request(xknx, 4)
        _prop_desc(xknx, ia, seq=3, object_index=0, property_id=0, property_index=1)  # inner idx=1: end
        await _wait_for_request(xknx, 5)
        _prop_desc(xknx, ia, seq=4, object_index=1, property_id=0, property_index=0)  # outer: no more

    responder = asyncio.create_task(respond())
    result = await dmp_interface_object_scan_r(conn)
    await responder

    assert len(result) == 1
    assert isinstance(result[0], ScannedInterfaceObject)
    assert result[0].object_index == 0
    assert result[0].object_type == 1
    assert len(result[0].properties) == 1
    assert result[0].properties[0].property_id == 78
    await conn.disconnect()


async def test_dmp_interface_object_scan_r_single_object_two_properties(xknx_setup: XKNX) -> None:
    """Test scan discovers one object with two properties."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _prop_desc(xknx, ia, seq=0, object_index=0, property_id=1, property_index=0)  # outer: exists
        await _wait_for_request(xknx, 2)
        _prop_val(xknx, ia, seq=1, object_index=0, property_id=1, data=b"\x00\x01")   # type read
        await _wait_for_request(xknx, 3)
        _prop_desc(xknx, ia, seq=2, object_index=0, property_id=1, property_index=0)  # inner idx=0: PID=1
        await _wait_for_request(xknx, 4)
        _prop_desc(xknx, ia, seq=3, object_index=0, property_id=78, property_index=1) # inner idx=1: PID=78
        await _wait_for_request(xknx, 5)
        _prop_desc(xknx, ia, seq=4, object_index=0, property_id=0, property_index=2)  # inner idx=2: end
        await _wait_for_request(xknx, 6)
        _prop_desc(xknx, ia, seq=5, object_index=1, property_id=0, property_index=0)  # outer: no more

    responder = asyncio.create_task(respond())
    result = await dmp_interface_object_scan_r(conn)
    await responder

    assert len(result) == 1
    assert result[0].object_index == 0
    assert result[0].object_type == 1
    assert len(result[0].properties) == 2
    assert result[0].properties[0].property_id == 1
    assert result[0].properties[1].property_id == 78
    await conn.disconnect()


async def test_dmp_interface_object_scan_r_multiple_objects(xknx_setup: XKNX) -> None:
    """Test scan discovers two objects with different types and property counts."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        # object 0: type=1, one property (PID=1)
        await _wait_for_request(xknx, 1)
        _prop_desc(xknx, ia, seq=0, object_index=0, property_id=1, property_index=0)
        await _wait_for_request(xknx, 2)
        _prop_val(xknx, ia, seq=1, object_index=0, property_id=1, data=b"\x00\x01")
        await _wait_for_request(xknx, 3)
        _prop_desc(xknx, ia, seq=2, object_index=0, property_id=1, property_index=0)
        await _wait_for_request(xknx, 4)
        _prop_desc(xknx, ia, seq=3, object_index=0, property_id=0, property_index=1)  # end of obj 0 properties
        # object 1: type=11, two properties (PID=1, PID=52)
        await _wait_for_request(xknx, 5)
        _prop_desc(xknx, ia, seq=4, object_index=1, property_id=1, property_index=0)
        await _wait_for_request(xknx, 6)
        _prop_val(xknx, ia, seq=5, object_index=1, property_id=1, data=b"\x00\x0B")
        await _wait_for_request(xknx, 7)
        _prop_desc(xknx, ia, seq=6, object_index=1, property_id=1, property_index=0)
        await _wait_for_request(xknx, 8)
        _prop_desc(xknx, ia, seq=7, object_index=1, property_id=52, property_index=1)
        await _wait_for_request(xknx, 9)
        _prop_desc(xknx, ia, seq=8, object_index=1, property_id=0, property_index=2)  # end of obj 1 properties
        # no more objects
        await _wait_for_request(xknx, 10)
        _prop_desc(xknx, ia, seq=9, object_index=2, property_id=0, property_index=0)

    responder = asyncio.create_task(respond())
    result = await dmp_interface_object_scan_r(conn)
    await responder

    assert len(result) == 2
    assert result[0].object_index == 0
    assert result[0].object_type == 1
    assert len(result[0].properties) == 1
    assert result[0].properties[0].property_id == 1

    assert result[1].object_index == 1
    assert result[1].object_type == 0x0B
    assert len(result[1].properties) == 2
    assert result[1].properties[0].property_id == 1
    assert result[1].properties[1].property_id == 52
    await conn.disconnect()


async def test_dmp_interface_object_scan_r_object_type_read_error(xknx_setup: XKNX) -> None:
    """Test scan raises ManagementConnectionError when object type read returns nr_of_elem=0."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _prop_desc(xknx, ia, seq=0, object_index=0, property_id=1, property_index=0)
        await _wait_for_request(xknx, 2)
        xknx.management.process(
            Telegram(
                source_address=ia,
                destination_address=xknx.current_address,
                direction=TelegramDirection.INCOMING,
                tpci=tpci.TAck(1),
            )
        )
        xknx.management.process(
            Telegram(
                source_address=ia,
                destination_address=xknx.current_address,
                direction=TelegramDirection.INCOMING,
                tpci=tpci.TDataConnected(1),
                payload=apci.PropertyValueResponse(
                    object_index=0, property_id=1, count=0, start_index=1, data=b""
                ),
            )
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="nr_of_elem=0"):
        await dmp_interface_object_scan_r(conn)
    await responder
    await conn.disconnect()
