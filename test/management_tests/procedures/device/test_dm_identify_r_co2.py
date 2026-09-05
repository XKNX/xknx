"""Tests for dm_identify_r_co2 — KNX v02.01.02 - Management Procedures 03.05.02 - §3.4.3."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dm_identify_r_co2 import (
    DeviceIdentity,
    dm_identify_r_co2,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci

RESPONDER_TIMEOUT = 1


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _process_response(
    xknx: XKNX, ia: IndividualAddress, seq: int, payload: apci.APCI
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
    async with asyncio.timeout(RESPONDER_TIMEOUT):
        while xknx.cemi_handler.send_telegram.call_count < threshold:  # noqa: ASYNC110
            await asyncio.sleep(0)


def _prop_response(property_id: int, data: bytes) -> apci.PropertyValueResponse:
    """Build a PropertyValueResponse for object_index=0."""
    return apci.PropertyValueResponse(
        object_index=0, property_id=property_id, count=1, start_index=1, data=data
    )


async def test_dm_identify_r_co2_success(xknx_setup: XKNX) -> None:
    """Test dm_identify_r_co2 reads manufacturer ID and hardware type."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(xknx, ia, seq=0, payload=_prop_response(12, b"\x00\x01"))
        await _wait_for_request(xknx, 2)
        _process_response(
            xknx,
            ia,
            seq=1,
            payload=_prop_response(78, bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05])),
        )

    responder = asyncio.create_task(respond())
    result = await dm_identify_r_co2(conn, device_descriptor_type_0=0x07B0)
    await responder

    assert result == DeviceIdentity(
        device_descriptor_type_0=0x07B0,
        manufacturer_id=1,
        hardware_type=bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05]),
    )
    assert xknx.cemi_handler.send_telegram.call_args_list[0].args[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.PropertyValueRead(
            object_index=0, property_id=12, count=1, start_index=1
        ),
    )
    assert xknx.cemi_handler.send_telegram.call_args_list[2].args[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(1),
        payload=apci.PropertyValueRead(
            object_index=0, property_id=78, count=1, start_index=1
        ),
    )
    await conn.disconnect()


async def test_dm_identify_r_co2_wrong_manufacturer_id_length(
    xknx_setup: XKNX,
) -> None:
    """Test dm_identify_r_co2 raises when PID_MANUFACTURER_ID isn't 2 octets."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(xknx, ia, seq=0, payload=_prop_response(12, b"\x01"))

    responder = asyncio.create_task(respond())
    with pytest.raises(
        ManagementConnectionError,
        match=r"PID_MANUFACTURER_ID returned 1 octets, expected 2",
    ):
        await dm_identify_r_co2(conn, device_descriptor_type_0=0x07B0)
    await responder

    await conn.disconnect()


async def test_dm_identify_r_co2_wrong_hardware_type_length(
    xknx_setup: XKNX,
) -> None:
    """Test dm_identify_r_co2 raises when PID_HARDWARE_TYPE isn't 6 octets."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(xknx, ia, seq=0, payload=_prop_response(12, b"\x00\x01"))
        await _wait_for_request(xknx, 2)
        _process_response(xknx, ia, seq=1, payload=_prop_response(78, bytes(5)))

    responder = asyncio.create_task(respond())
    with pytest.raises(
        ManagementConnectionError,
        match=r"PID_HARDWARE_TYPE returned 5 octets, expected 6",
    ):
        await dm_identify_r_co2(conn, device_descriptor_type_0=0x07B0)
    await responder

    await conn.disconnect()
