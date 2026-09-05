"""Tests for dmp_load_state_machine_verify_r_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.32.3."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import VerificationError
from xknx.management.procedures.device.dmp_load_state_machine_verify_r_io import (
    dmp_load_state_machine_verify_r_io,
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


def _load_state_response(
    object_index: int, state: LoadState
) -> apci.PropertyValueResponse:
    """Build the PropertyValueResponse a Load State Machine read returns."""
    return apci.PropertyValueResponse(
        object_index=object_index,
        property_id=5,  # PID_LOAD_STATE_CONTROL
        count=1,
        start_index=1,
        data=bytes([state]),
    )


async def test_dmp_load_state_machine_verify_r_io_matches(xknx_setup: XKNX) -> None:
    """Test the procedure returns None when the read state matches expected_state."""
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
            payload=_load_state_response(3, LoadState.LOADED),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    result = await dmp_load_state_machine_verify_r_io(
        conn, object_index=3, expected_state=LoadState.LOADED
    )
    await responder

    assert result is None
    await conn.disconnect()


async def test_dmp_load_state_machine_verify_r_io_mismatch(xknx_setup: XKNX) -> None:
    """Test the procedure raises VerificationError when the read state doesn't match."""
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
            payload=_load_state_response(3, LoadState.LOADING),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(VerificationError, match=r"expected LOADED, got LOADING"):
        await dmp_load_state_machine_verify_r_io(
            conn, object_index=3, expected_state=LoadState.LOADED
        )
    await responder

    await conn.disconnect()
