"""Tests for dmp_download_loadable_part_r_co_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.4."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_download_loadable_part_r_co_io import (
    dmp_download_loadable_part_r_co_io,
)
from xknx.management.procedures.device.load_state import (
    LoadState,
    load_completed,
    start_loading,
    unload,
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


def _load_state_response(
    object_index: int, state: LoadState
) -> apci.PropertyValueResponse:
    """Build the PropertyValueResponse a Load State Machine write returns."""
    return apci.PropertyValueResponse(
        object_index=object_index,
        property_id=5,  # PID_LOAD_STATE_CONTROL
        count=1,
        start_index=1,
        data=bytes([state]),
    )


async def _next_request_telegram(xknx: XKNX, start: int) -> tuple[int, Telegram]:
    """Return (index after, telegram) of the next outgoing Write/Read at or after start, skipping our own ACKs."""
    idx = start
    while True:
        async with asyncio.timeout(RESPONDER_TIMEOUT):
            while len(xknx.cemi_handler.send_telegram.call_args_list) <= idx:  # noqa: ASYNC110
                await asyncio.sleep(0)
        telegram = xknx.cemi_handler.send_telegram.call_args_list[idx].args[0]
        idx += 1
        if isinstance(
            telegram.payload, apci.PropertyValueWrite | apci.PropertyValueRead
        ):
            return idx, telegram


def _sent_events(xknx: XKNX) -> list[bytes]:
    """Return the event data of every outgoing PropertyValueWrite, in order."""
    return [
        call.args[0].payload.data
        for call in xknx.cemi_handler.send_telegram.call_args_list
        if isinstance(call.args[0].payload, apci.PropertyValueWrite)
    ]


async def _respond_in_sequence(
    xknx: XKNX, ia: IndividualAddress, states: list[LoadState]
) -> None:
    """Answer each outgoing PropertyValueWrite/Read in turn with the next state in states."""
    idx = 0
    for response_seq, state in enumerate(states):
        idx, telegram = await _next_request_telegram(xknx, idx)
        _process_response(
            xknx,
            ia,
            ack_seq=telegram.tpci.sequence_number,
            payload=_load_state_response(2, state),
            response_seq=response_seq,
        )


async def test_dmp_download_loadable_part_r_co_io_success_no_additional_controls(
    xknx_setup: XKNX,
) -> None:
    """Test the full sequence: Unload, Start Loading, load_data, Load Completed."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    load_data = AsyncMock()

    responder = asyncio.create_task(
        _respond_in_sequence(
            xknx,
            ia,
            [LoadState.UNLOADED, LoadState.LOADING, LoadState.LOADED],
        )
    )
    await dmp_download_loadable_part_r_co_io(conn, object_index=2, load_data=load_data)
    await responder

    assert _sent_events(xknx) == [unload(), start_loading(), load_completed()]
    load_data.assert_awaited_once()
    await conn.disconnect()


async def test_dmp_download_loadable_part_r_co_io_success_with_additional_controls(
    xknx_setup: XKNX,
) -> None:
    """Test additional_load_controls events are sent between Start Loading and load_data."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    load_data = AsyncMock()

    responder = asyncio.create_task(
        _respond_in_sequence(
            xknx,
            ia,
            [
                LoadState.UNLOADED,
                LoadState.LOADING,
                LoadState.LOADING,
                LoadState.LOADING,
                LoadState.LOADED,
            ],
        )
    )
    control_1 = bytes([0x03, 0x00]) + bytes(8)
    control_2 = bytes([0x03, 0x01]) + bytes(8)
    await dmp_download_loadable_part_r_co_io(
        conn,
        object_index=2,
        load_data=load_data,
        additional_load_controls=[control_1, control_2],
    )
    await responder

    assert _sent_events(xknx) == [
        unload(),
        start_loading(),
        control_1,
        control_2,
        load_completed(),
    ]
    load_data.assert_awaited_once()
    await conn.disconnect()


async def test_dmp_download_loadable_part_r_co_io_unload_polls_until_unloaded(
    xknx_setup: XKNX,
) -> None:
    """Test the Unload step polls (re-reads) until UNLOADED is reached."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    load_data = AsyncMock()

    # Unload's own write response comes back UNLOADING, the poll read
    # reaches UNLOADED, then Start Loading and Load Completed follow as usual.
    responder = asyncio.create_task(
        _respond_in_sequence(
            xknx,
            ia,
            [
                LoadState.UNLOADING,
                LoadState.UNLOADED,
                LoadState.LOADING,
                LoadState.LOADED,
            ],
        )
    )
    await dmp_download_loadable_part_r_co_io(
        conn,
        object_index=2,
        load_data=load_data,
        unload_poll_timeout=1.0,
        unload_poll_interval=0.01,
    )
    await responder

    load_data.assert_awaited_once()
    await conn.disconnect()


async def test_dmp_download_loadable_part_r_co_io_unload_timeout(
    xknx_setup: XKNX,
) -> None:
    """Test the procedure raises when Unload never reaches UNLOADED within unload_poll_timeout."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    load_data = AsyncMock()

    async def respond() -> None:
        # Answers every outgoing PropertyValueWrite/Read with UNLOADING
        # (never UNLOADED), until the caller stops sending new requests (the
        # unload_poll_timeout below elapsed) and this naturally times out.
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
                payload=_load_state_response(2, LoadState.UNLOADING),
                response_seq=response_seq,
            )
            response_seq += 1

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match=r"did not reach UNLOADED"):
        await dmp_download_loadable_part_r_co_io(
            conn,
            object_index=2,
            load_data=load_data,
            unload_poll_timeout=0.3,
            unload_poll_interval=0.05,
        )
    await responder

    load_data.assert_not_awaited()
    await conn.disconnect()


async def test_dmp_download_loadable_part_r_co_io_start_loading_wrong_state_raises(
    xknx_setup: XKNX,
) -> None:
    """Test the procedure raises when Start Loading's response isn't LOADING."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    load_data = AsyncMock()

    responder = asyncio.create_task(
        _respond_in_sequence(xknx, ia, [LoadState.UNLOADED, LoadState.ERROR])
    )
    with pytest.raises(
        ManagementConnectionError,
        match=r"Start Loading failed: expected LOADING, got ERROR",
    ):
        await dmp_download_loadable_part_r_co_io(
            conn, object_index=2, load_data=load_data
        )
    await responder

    load_data.assert_not_awaited()
    await conn.disconnect()


async def test_dmp_download_loadable_part_r_co_io_additional_control_wrong_state_raises(
    xknx_setup: XKNX,
) -> None:
    """Test the procedure raises when an additional load control's response isn't LOADING."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    load_data = AsyncMock()

    responder = asyncio.create_task(
        _respond_in_sequence(
            xknx, ia, [LoadState.UNLOADED, LoadState.LOADING, LoadState.ERROR]
        )
    )
    with pytest.raises(
        ManagementConnectionError,
        match=r"Additional Load Control failed: expected LOADING, got ERROR",
    ):
        await dmp_download_loadable_part_r_co_io(
            conn,
            object_index=2,
            load_data=load_data,
            additional_load_controls=[bytes([0x03, 0x00]) + bytes(8)],
        )
    await responder

    load_data.assert_not_awaited()
    await conn.disconnect()


async def test_dmp_download_loadable_part_r_co_io_load_completed_wrong_state_raises(
    xknx_setup: XKNX,
) -> None:
    """Test the procedure raises when Load Completed's response isn't LOADED."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    load_data = AsyncMock()

    responder = asyncio.create_task(
        _respond_in_sequence(
            xknx, ia, [LoadState.UNLOADED, LoadState.LOADING, LoadState.ERROR]
        )
    )
    with pytest.raises(
        ManagementConnectionError,
        match=r"Load Completed failed: expected LOADED, got ERROR",
    ):
        await dmp_download_loadable_part_r_co_io(
            conn, object_index=2, load_data=load_data
        )
    await responder

    load_data.assert_awaited_once()
    await conn.disconnect()
