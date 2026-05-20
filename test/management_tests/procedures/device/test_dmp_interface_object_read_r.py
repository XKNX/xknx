"""Tests for dmp_interface_object_read_r — KNX 03.05.02 §3.27.2."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_interface_object_read_r import (
    dmp_interface_object_read_r,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


@pytest.fixture
def xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


async def test_dmp_interface_object_read_r_basic(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_read_r reads property value."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        while xknx.cemi_handler.send_telegram.call_count < 1:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(0),
        )
        response = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(0),
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=78,
                count=1,
                start_index=1,
                data=b"\x00\x91",
            ),
        )
        xknx.management.process(ack)
        xknx.management.process(response)

    responder = asyncio.create_task(respond())
    data = await dmp_interface_object_read_r(
        conn, object_index=0, property_id=78, count=1, start_index=1
    )
    await responder

    assert data == b"\x00\x91"
    await conn.disconnect()


async def test_dmp_interface_object_read_r_multiple_elements(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_read_r with count > 1."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        while xknx.cemi_handler.send_telegram.call_count < 1:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(0),
        )
        response = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(0),
            payload=apci.PropertyValueResponse(
                object_index=1,
                property_id=52,
                count=3,
                start_index=1,
                data=b"\x01\x02\x03\x04\x05\x06",
            ),
        )
        xknx.management.process(ack)
        xknx.management.process(response)

    responder = asyncio.create_task(respond())
    data = await dmp_interface_object_read_r(
        conn, object_index=1, property_id=52, count=3, start_index=1
    )
    await responder

    assert data == b"\x01\x02\x03\x04\x05\x06"
    await conn.disconnect()


async def test_dmp_interface_object_read_r_empty(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_read_r with count=0 returns empty bytes."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    data = await dmp_interface_object_read_r(
        conn, object_index=0, property_id=78, count=0
    )

    assert data == b""
    await conn.disconnect()


async def test_dmp_interface_object_read_r_chunked(xknx_setup: XKNX) -> None:
    """Test dmp_interface_object_read_r with count > 15 uses multiple requests."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        while xknx.cemi_handler.send_telegram.call_count < 1:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack0 = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(0),
        )
        response0 = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(0),
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=52,
                count=15,
                start_index=1,
                data=b"\x01" * 15,
            ),
        )
        xknx.management.process(ack0)
        xknx.management.process(response0)

        while xknx.cemi_handler.send_telegram.call_count < 3:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack1 = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(1),
        )
        response1 = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(1),
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=52,
                count=5,
                start_index=16,
                data=b"\x02" * 5,
            ),
        )
        xknx.management.process(ack1)
        xknx.management.process(response1)

    responder = asyncio.create_task(respond())
    data = await dmp_interface_object_read_r(
        conn, object_index=0, property_id=52, count=20, start_index=1
    )
    await responder

    assert data == b"\x01" * 15 + b"\x02" * 5
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
        while xknx.cemi_handler.send_telegram.call_count < 1:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(0),
        )
        response = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(0),
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=52,
                count=2,  # requested 5, got 2
                start_index=1,
                data=b"\x01\x02",
            ),
        )
        xknx.management.process(ack)
        xknx.management.process(response)

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
        while xknx.cemi_handler.send_telegram.call_count < 1:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(0),
        )
        response = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(0),
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=78,
                count=0,
                start_index=1,
                data=b"",
            ),
        )
        xknx.management.process(ack)
        xknx.management.process(response)

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"nr_of_elem=0"):
        await dmp_interface_object_read_r(
            conn, object_index=0, property_id=78, count=1, start_index=1
        )
    await responder

    await conn.disconnect()
