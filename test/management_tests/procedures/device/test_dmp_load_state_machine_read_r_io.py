"""Tests for dmp_load_state_machine_read_r_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.33.3."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_load_state_machine_read_r_io import (
    dmp_load_state_machine_read_r_io,
)
from xknx.management.procedures.device.load_state import LoadState
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci

RESPONDER_TIMEOUT = 1


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _process_response(
    xknx: XKNX,
    ia: IndividualAddress,
    ack_seq: int,
    payload: apci.APCI,
    response_seq: int,
) -> None:
    """Inject ACK + TDataConnected response into the management layer."""
    xknx.management.process(
        Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(ack_seq),
        )
    )
    xknx.management.process(
        Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(response_seq),
            payload=payload,
        )
    )


async def _wait_for_calls(xknx: XKNX, count: int) -> None:
    """Wait until at least count telegrams have been sent."""
    async with asyncio.timeout(RESPONDER_TIMEOUT):
        while xknx.cemi_handler.send_telegram.call_count < count:  # noqa: ASYNC110
            await asyncio.sleep(0)


def _load_state_response(object_index: int, data: bytes) -> apci.PropertyValueResponse:
    """Build the PropertyValueResponse a Load State Machine read returns."""
    return apci.PropertyValueResponse(
        object_index=object_index,
        property_id=5,  # PID_LOAD_STATE_CONTROL
        count=1,
        start_index=1,
        data=data,
    )


async def test_dmp_load_state_machine_read_r_io_success(xknx_setup: XKNX) -> None:
    """Test the procedure reads and decodes the current Load State."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process_response(
            xknx,
            ia,
            ack_seq=0,
            payload=_load_state_response(3, bytes([LoadState.LOADED])),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    state = await dmp_load_state_machine_read_r_io(conn, object_index=3)
    await responder

    assert state == LoadState.LOADED
    assert xknx.cemi_handler.send_telegram.call_args_list[0].args[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.PropertyValueRead(
            object_index=3, property_id=5, count=1, start_index=1
        ),
    )
    await conn.disconnect()


async def test_dmp_load_state_machine_read_r_io_unknown_state(
    xknx_setup: XKNX,
) -> None:
    """Test the procedure raises when the device reports an undefined state value."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process_response(
            xknx,
            ia,
            ack_seq=0,
            payload=_load_state_response(3, bytes([0xFF])),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"unknown state 0xff"):
        await dmp_load_state_machine_read_r_io(conn, object_index=3)
    await responder

    await conn.disconnect()


async def test_dmp_load_state_machine_read_r_io_echoed_event_not_state(
    xknx_setup: XKNX,
) -> None:
    """
    Test the procedure raises when the response carries more than 1 octet.

    A misbehaving device answering with a 10 octet load event (rather than
    the 1 octet Load State) must not have its event type byte silently
    misread as a Load State value.
    """
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process_response(
            xknx,
            ia,
            ack_seq=0,
            payload=_load_state_response(3, bytes([0x01]) + bytes(9)),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(
        ManagementConnectionError, match=r"returned 10 octets, expected 1"
    ):
        await dmp_load_state_machine_read_r_io(conn, object_index=3)
    await responder

    await conn.disconnect()
