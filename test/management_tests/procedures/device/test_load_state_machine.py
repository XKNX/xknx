"""Tests for the DM_LoadStateMachine* procedures — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31-§3.33."""

import asyncio
from collections.abc import Sequence
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.management import P2PConnection
from xknx.management.procedures import (
    dm_load_state_machine_verify_r_co_mem,
    dm_load_state_machine_verify_r_io,
    dmp_download_loadable_part_r_co_io,
    dmp_ext_load_state_machine_read_r_co_io,
    dmp_ext_load_state_machine_verify_r_co_io,
    dmp_ext_load_state_machine_write_r_co_io,
    dmp_load_state_machine_read_r_co_mem,
    dmp_load_state_machine_read_r_io,
    dmp_load_state_machine_write_r_co_io,
    dmp_load_state_machine_write_r_co_mem,
    dmp_mem_write_r_co,
)
from xknx.profile.const import LoadEvent, LoadState, ResourceObjectType
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci

IA = IndividualAddress("4.0.10")
PID_LOAD_STATE_CONTROL = 5


@pytest.fixture(name="xknx")
def fixture_xknx() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _sent_requests(xknx: XKNX) -> list[apci.APCI]:
    """Return the payloads of the connected data telegrams sent so far."""
    return [
        call.args[0].payload
        for call in xknx.cemi_handler.send_telegram.call_args_list
        if isinstance(call.args[0].tpci, tpci.TDataConnected)
    ]


def _incoming(xknx: XKNX, tpdu: tpci.TPCI, payload: apci.APCI | None = None) -> None:
    xknx.management.process(
        Telegram(
            source_address=IA,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpdu,
            payload=payload,
        )
    )


async def _serve(xknx: XKNX, replies: Sequence[apci.APCI | None]) -> None:
    """Acknowledge each request in turn and answer it with its reply (None = ack only)."""
    device_seq = 0
    for our_seq, reply in enumerate(replies):
        async with asyncio.timeout(1):
            while len(_sent_requests(xknx)) <= our_seq:  # noqa: ASYNC110
                await asyncio.sleep(0)
        _incoming(xknx, tpci.TAck(our_seq))
        if reply is not None:
            _incoming(xknx, tpci.TDataConnected(device_seq), reply)
            device_seq += 1


async def _connect(xknx: XKNX) -> P2PConnection:
    conn = await xknx.management.connect(IA)
    xknx.cemi_handler.send_telegram.reset_mock()
    return conn


def _property_response(data: bytes, count: int = 1) -> apci.PropertyValueResponse:
    return apci.PropertyValueResponse(
        object_index=3,
        property_id=PID_LOAD_STATE_CONTROL,
        count=count,
        start_index=1,
        data=data,
    )


def _ext_response(
    data: bytes, return_code: apci.ReturnCode = apci.ReturnCode.E_SUCCESS
) -> apci.FunctionPropertyExtStateResponse:
    return apci.FunctionPropertyExtStateResponse(
        interface_object_type=ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
        object_instance=1,
        property_id=PID_LOAD_STATE_CONTROL,
        return_code=return_code,
        data=data,
    )


def _memory_response(state: int, address: int = 0xB6EC) -> apci.MemoryResponse:
    return apci.MemoryResponse(address=address, data=bytes([state]))


async def test_read_r_io(xknx: XKNX) -> None:
    """Test reading the state of a property based Load State Machine."""
    conn = await _connect(xknx)
    server = asyncio.create_task(_serve(xknx, [_property_response(b"\x01")]))
    assert await dmp_load_state_machine_read_r_io(conn, 3) is LoadState.LOADED
    await server
    assert _sent_requests(xknx) == [
        apci.PropertyValueRead(
            object_index=3, property_id=PID_LOAD_STATE_CONTROL, count=1, start_index=1
        )
    ]


@pytest.mark.parametrize(
    "response", [_property_response(b"", count=0), _property_response(b"\x07")]
)
async def test_read_r_io_errors(
    xknx: XKNX, response: apci.PropertyValueResponse
) -> None:
    """Test a missing Property and an unknown state."""
    conn = await _connect(xknx)
    server = asyncio.create_task(_serve(xknx, [response]))
    with pytest.raises(ManagementConnectionError):
        await dmp_load_state_machine_read_r_io(conn, 3)
    await server


async def test_verify_r_io(xknx: XKNX) -> None:
    """Test verifying the state of a property based Load State Machine."""
    conn = await _connect(xknx)
    server = asyncio.create_task(
        _serve(xknx, [_property_response(b"\x01"), _property_response(b"\x00")])
    )
    await dm_load_state_machine_verify_r_io(conn, 3, LoadState.LOADED)
    with pytest.raises(VerificationError):
        await dm_load_state_machine_verify_r_io(conn, 3, LoadState.LOADED)
    await server


async def test_write_r_co_io(xknx: XKNX) -> None:
    """Test sending an event: 10 octets of load control, the state is returned."""
    conn = await _connect(xknx)
    server = asyncio.create_task(_serve(xknx, [_property_response(b"\x02")]))
    state = await dmp_load_state_machine_write_r_co_io(conn, 3, LoadEvent.START_LOADING)
    await server
    assert state is LoadState.LOADING
    assert _sent_requests(xknx) == [
        apci.PropertyValueWrite(
            object_index=3,
            property_id=PID_LOAD_STATE_CONTROL,
            count=1,
            start_index=1,
            data=b"\x01" + bytes(9),
        )
    ]


async def test_write_r_co_io_event_data(xknx: XKNX) -> None:
    """Test an Additional Load Control with its sub type and data."""
    conn = await _connect(xknx)
    server = asyncio.create_task(_serve(xknx, [_property_response(b"\x02")]))
    await dmp_load_state_machine_write_r_co_io(
        conn, 3, LoadEvent.ADDITIONAL_LOAD_CONTROLS, b"\x0a\x01\x00", verify=True
    )
    await server
    assert _sent_requests(xknx)[0].data == b"\x03\x0a\x01\x00" + bytes(6)


async def test_write_r_co_io_waits_for_intermediate_state(xknx: XKNX) -> None:
    """Test that verify reads again while the state is LoadCompleting."""
    conn = await _connect(xknx)
    server = asyncio.create_task(
        _serve(
            xknx,
            [
                _property_response(b"\x05"),
                _property_response(b"\x05"),
                _property_response(b"\x01"),
            ],
        )
    )
    state = await dmp_load_state_machine_write_r_co_io(
        conn, 3, LoadEvent.LOAD_COMPLETED, verify=True, poll_interval=0
    )
    await server
    assert state is LoadState.LOADED
    assert len(_sent_requests(xknx)) == 3


async def test_write_r_co_io_verify_fails(xknx: XKNX) -> None:
    """Test that verify rejects a wrong resulting state."""
    conn = await _connect(xknx)
    server = asyncio.create_task(_serve(xknx, [_property_response(b"\x03")]))
    with pytest.raises(VerificationError):
        await dmp_load_state_machine_write_r_co_io(
            conn, 3, LoadEvent.LOAD_COMPLETED, verify=True
        )
    await server


async def test_write_r_co_io_event_data_too_long(xknx: XKNX) -> None:
    """Test that event data longer than 9 octets is rejected before sending."""
    conn = await _connect(xknx)
    with pytest.raises(ValueError):
        await dmp_load_state_machine_write_r_co_io(
            conn, 3, LoadEvent.ADDITIONAL_LOAD_CONTROLS, bytes(10)
        )
    assert _sent_requests(xknx) == []


async def test_read_r_co_mem(xknx: XKNX) -> None:
    """Test reading a memory mapped Load State Machine of a BIM M112."""
    conn = await _connect(xknx)
    server = asyncio.create_task(_serve(xknx, [_memory_response(1)]))
    state = await dmp_load_state_machine_read_r_co_mem(
        conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM
    )
    await server
    assert state is LoadState.LOADED
    assert _sent_requests(xknx) == [apci.MemoryRead(address=0xB6EC, count=1)]


async def test_read_r_co_mem_invalid_state_machine(xknx: XKNX) -> None:
    """Test that only the four memory mapped state machine types are accepted."""
    conn = await _connect(xknx)
    with pytest.raises(ValueError):
        await dmp_load_state_machine_read_r_co_mem(
            conn, ResourceObjectType.OBJECT_DEVICE
        )


async def test_verify_r_co_mem(xknx: XKNX) -> None:
    """Test verifying a memory mapped Load State Machine."""
    conn = await _connect(xknx)
    server = asyncio.create_task(_serve(xknx, [_memory_response(2)]))
    with pytest.raises(VerificationError):
        await dm_load_state_machine_verify_r_co_mem(
            conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, LoadState.LOADED
        )
    await server


async def test_write_r_co_mem(xknx: XKNX) -> None:
    """Test the management control at 0104h, then reading until the state is reached."""
    conn = await _connect(xknx)
    server = asyncio.create_task(
        _serve(xknx, [None, _memory_response(2), _memory_response(1)])
    )
    state = await dmp_load_state_machine_write_r_co_mem(
        conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, LoadEvent.LOAD_COMPLETED
    )
    await server
    assert state is LoadState.LOADED
    requests = _sent_requests(xknx)
    assert requests[0] == apci.MemoryWrite(address=0x0104, data=b"\x32" + bytes(10))
    assert requests[1:] == [apci.MemoryRead(address=0xB6EC, count=1)] * 2


async def test_write_r_co_mem_reads_at_most_three_times(xknx: XKNX) -> None:
    """Test that the state is read at most three times."""
    conn = await _connect(xknx)
    server = asyncio.create_task(
        _serve(
            xknx,
            [
                None,
                _memory_response(2, 0xB6EA),
                _memory_response(2, 0xB6EA),
                _memory_response(2, 0xB6EA),
            ],
        )
    )
    with pytest.raises(VerificationError):
        await dmp_load_state_machine_write_r_co_mem(
            conn, ResourceObjectType.OBJECT_ADDRESS_TABLE, LoadEvent.LOAD_COMPLETED
        )
    await server
    assert _sent_requests(xknx)[0].data[0] == 0x12


async def test_ext_read_r_co_io(xknx: XKNX) -> None:
    """Test reading a Load State Machine with A_FunctionPropertyExtState_Read."""
    conn = await _connect(xknx)
    server = asyncio.create_task(_serve(xknx, [_ext_response(b"\x01")]))
    state = await dmp_ext_load_state_machine_read_r_co_io(
        conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, 1
    )
    await server
    assert state is LoadState.LOADED
    assert _sent_requests(xknx) == [
        apci.FunctionPropertyExtStateRead(
            interface_object_type=ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
            object_instance=1,
            property_id=PID_LOAD_STATE_CONTROL,
        )
    ]


async def test_ext_read_r_co_io_negative_return_code(xknx: XKNX) -> None:
    """Test that a negative return code is an error."""
    conn = await _connect(xknx)
    server = asyncio.create_task(
        _serve(xknx, [_ext_response(b"", apci.ReturnCode.E_COMMAND_INVALID)])
    )
    with pytest.raises(ManagementConnectionError):
        await dmp_ext_load_state_machine_read_r_co_io(
            conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, 1
        )
    await server


async def test_ext_verify_r_co_io(xknx: XKNX) -> None:
    """Test verifying a Load State Machine with A_FunctionPropertyExtState_Read."""
    conn = await _connect(xknx)
    server = asyncio.create_task(_serve(xknx, [_ext_response(b"\x00")]))
    await dmp_ext_load_state_machine_verify_r_co_io(
        conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, 1, LoadState.UNLOADED
    )
    await server


async def test_ext_write_r_co_io(xknx: XKNX) -> None:
    """Test sending an event with A_FunctionPropertyExtCommand."""
    conn = await _connect(xknx)
    server = asyncio.create_task(_serve(xknx, [_ext_response(b"\x00")]))
    state = await dmp_ext_load_state_machine_write_r_co_io(
        conn,
        ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
        1,
        LoadEvent.UNLOAD,
        verify=True,
    )
    await server
    assert state is LoadState.UNLOADED
    assert _sent_requests(xknx) == [
        apci.FunctionPropertyExtCommand(
            interface_object_type=ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
            object_instance=1,
            property_id=PID_LOAD_STATE_CONTROL,
            data=b"\x04" + bytes(9),
        )
    ]


def _write(event: int, data: bytes = b"") -> apci.PropertyValueWrite:
    return apci.PropertyValueWrite(
        object_index=3,
        property_id=PID_LOAD_STATE_CONTROL,
        count=1,
        start_index=1,
        data=bytes([event]) + data.ljust(9, b"\x00"),
    )


async def test_download_loadable_part(xknx: XKNX) -> None:
    """Test the complete download sequence of one loadable part."""
    conn = await _connect(xknx)
    server = asyncio.create_task(
        _serve(
            xknx,
            [
                _property_response(b"\x00"),  # Unload -> Unloaded
                _property_response(b"\x02"),  # Start Loading -> Loading
                _property_response(b"\x02"),  # Additional Load Control -> Loading
                None,  # data written by `load`
                _property_response(b"\x01"),  # Load Completed -> Loaded
            ],
        )
    )

    async def load() -> None:
        await dmp_mem_write_r_co(conn, 0x4000, b"\x01\x02")

    await dmp_download_loadable_part_r_co_io(
        conn, 3, load, additional_load_controls=[b"\x0a\x00\x20"]
    )
    await server
    assert _sent_requests(xknx) == [
        _write(0x04),
        _write(0x01),
        _write(0x03, b"\x0a\x00\x20"),
        apci.MemoryWrite(address=0x4000, data=b"\x01\x02"),
        _write(0x02),
    ]


async def test_download_loadable_part_intermediate_states(xknx: XKNX) -> None:
    """Test that Unloading and LoadCompleting are read again until they end."""
    conn = await _connect(xknx)
    server = asyncio.create_task(
        _serve(
            xknx,
            [
                _property_response(b"\x04"),  # Unload -> Unloading
                _property_response(b"\x00"),  # read -> Unloaded
                _property_response(b"\x02"),  # Start Loading -> Loading
                _property_response(b"\x05"),  # Load Completed -> LoadCompleting
                _property_response(b"\x01"),  # read -> Loaded
            ],
        )
    )
    load = AsyncMock()
    await dmp_download_loadable_part_r_co_io(conn, 3, load, poll_interval=0)
    await server
    load.assert_awaited_once()


async def test_download_loadable_part_without_unload(xknx: XKNX) -> None:
    """Test that the Unload step is optional."""
    conn = await _connect(xknx)
    server = asyncio.create_task(
        _serve(xknx, [_property_response(b"\x02"), _property_response(b"\x01")])
    )
    await dmp_download_loadable_part_r_co_io(conn, 3, AsyncMock(), unload=False)
    await server
    assert _sent_requests(xknx) == [_write(0x01), _write(0x02)]


async def test_download_loadable_part_stops_on_wrong_state(xknx: XKNX) -> None:
    """Test that a step not leading to the expected state stops the download."""
    conn = await _connect(xknx)
    server = asyncio.create_task(
        _serve(xknx, [_property_response(b"\x00"), _property_response(b"\x03")])
    )
    load = AsyncMock()
    with pytest.raises(VerificationError):
        await dmp_download_loadable_part_r_co_io(conn, 3, load)
    await server
    load.assert_not_awaited()


async def test_download_loadable_part_control_too_long(xknx: XKNX) -> None:
    """Test that an additional load control longer than 9 octets is rejected first."""
    conn = await _connect(xknx)
    with pytest.raises(ValueError):
        await dmp_download_loadable_part_r_co_io(
            conn, 3, AsyncMock(), additional_load_controls=[bytes(10)]
        )
    assert _sent_requests(xknx) == []
