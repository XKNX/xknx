"""Tests for dmp_run_state_machine_write_r_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.34.3."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_run_state_machine_write_r_io import (
    dmp_run_state_machine_write_r_io,
)
from xknx.management.procedures.device.run_state import RunState, restart
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


def _run_state_response(
    object_index: int, state: RunState
) -> apci.PropertyValueResponse:
    """Build the PropertyValueResponse a Run State Machine write/read returns."""
    return apci.PropertyValueResponse(
        object_index=object_index,
        property_id=6,  # PID_RUN_STATE_CONTROL
        count=1,
        start_index=1,
        data=bytes([state]),
    )


async def test_dmp_run_state_machine_write_r_io_no_expected_state(
    xknx_setup: XKNX,
) -> None:
    """Test the procedure returns the write's own resulting state without polling."""
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
            payload=_run_state_response(2, RunState.STARTING),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    state = await dmp_run_state_machine_write_r_io(
        conn, object_index=2, event_data=restart()
    )
    await responder

    assert state == RunState.STARTING
    assert xknx.cemi_handler.send_telegram.call_args_list[0].args[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.PropertyValueWrite(
            object_index=2,
            property_id=6,
            count=1,
            start_index=1,
            data=restart(),
        ),
    )
    await conn.disconnect()


async def test_dmp_run_state_machine_write_r_io_wrong_event_length(
    xknx_setup: XKNX,
) -> None:
    """Test the procedure raises ValueError for event_data that isn't 10 octets."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"event_data must be 10 octets, got 3"):
        await dmp_run_state_machine_write_r_io(
            conn, object_index=2, event_data=b"\x01\x00\x00"
        )
    await conn.disconnect()


async def test_dmp_run_state_machine_write_r_io_expected_state_matches_immediately(
    xknx_setup: XKNX,
) -> None:
    """Test no polling happens when the write's own response already matches expected_state."""
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
            payload=_run_state_response(2, RunState.RUNNING),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    state = await dmp_run_state_machine_write_r_io(
        conn,
        object_index=2,
        event_data=restart(),
        expected_state=RunState.RUNNING,
    )
    await responder

    assert state == RunState.RUNNING
    # only the write - no poll read
    assert (
        xknx.cemi_handler.send_telegram.call_count == 2
    )  # write + our ack of response
    await conn.disconnect()


async def test_dmp_run_state_machine_write_r_io_polls_until_match(
    xknx_setup: XKNX,
) -> None:
    """Test the procedure polls (re-reads) until the state matches expected_state."""
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
            payload=_run_state_response(2, RunState.STARTING),
            response_seq=0,
        )
        await _wait_for_calls(xknx, 3)
        _process_response(
            xknx,
            ia,
            ack_seq=1,
            payload=_run_state_response(2, RunState.RUNNING),
            response_seq=1,
        )

    responder = asyncio.create_task(respond())
    state = await dmp_run_state_machine_write_r_io(
        conn,
        object_index=2,
        event_data=restart(),
        expected_state=RunState.RUNNING,
        poll_interval=0.01,
        poll_timeout=1.0,
    )
    await responder

    assert state == RunState.RUNNING
    await conn.disconnect()


async def test_dmp_run_state_machine_write_r_io_poll_timeout(
    xknx_setup: XKNX,
) -> None:
    """Test the procedure raises after poll_timeout without reaching expected_state."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        # Answers every outgoing PropertyValueWrite/Read with STARTING (never
        # RUNNING), until the caller stops sending new requests (the
        # poll_timeout below elapsed) and this naturally times out.
        responded = 0
        response_seq = 0
        while True:
            calls = xknx.cemi_handler.send_telegram.call_args_list
            try:
                async with asyncio.timeout(0.5):
                    while len(calls) <= responded:  # noqa: ASYNC110
                        await asyncio.sleep(0)
            except TimeoutError:
                return
            telegram = calls[responded].args[0]
            responded += 1
            if not isinstance(
                telegram.payload, apci.PropertyValueWrite | apci.PropertyValueRead
            ):
                continue  # our own ACK of a previous response
            _process_response(
                xknx,
                ia,
                ack_seq=telegram.tpci.sequence_number,
                payload=_run_state_response(2, RunState.STARTING),
                response_seq=response_seq,
            )
            response_seq += 1

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"did not reach RUNNING"):
        await dmp_run_state_machine_write_r_io(
            conn,
            object_index=2,
            event_data=restart(),
            expected_state=RunState.RUNNING,
            poll_interval=0.05,
            poll_timeout=0.3,
        )
    await responder

    await conn.disconnect()


async def test_dmp_run_state_machine_write_r_io_unknown_state(
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
            payload=apci.PropertyValueResponse(
                object_index=2,
                property_id=6,
                count=1,
                start_index=1,
                data=bytes([0xFF]),
            ),
            response_seq=0,
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"unknown state 0xff"):
        await dmp_run_state_machine_write_r_io(
            conn, object_index=2, event_data=restart()
        )
    await responder

    await conn.disconnect()
