"""Tests for dmp_load_state_machine_write_r_co_mem — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.2."""

from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import VerificationError
from xknx.management.procedures.device.dmp_load_state_machine_write_r_co_mem import (
    dmp_load_state_machine_write_r_co_mem,
)
from xknx.profile.const import LoadEvent, LoadState, ResourceObjectType
from xknx.telegram import apci

from .load_state_machine_helpers import connect, memory_response, sent_requests


@pytest.fixture(name="xknx")
def fixture_xknx() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


async def test_dmp_load_state_machine_write_r_co_mem(xknx: XKNX) -> None:
    """Test the management control at 0104h, then reading until the state is reached."""
    conn = await connect(xknx, [None, memory_response(2), memory_response(1)])
    state = await dmp_load_state_machine_write_r_co_mem(
        conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, LoadEvent.LOAD_COMPLETED
    )
    assert state is LoadState.LOADED
    assert sent_requests(xknx) == [
        apci.MemoryWrite(address=0x0104, data=b"\x32" + bytes(10)),
        apci.MemoryRead(address=0xB6EC, count=1),
        apci.MemoryRead(address=0xB6EC, count=1),
    ]


async def test_dmp_load_state_machine_write_r_co_mem_event_data(xknx: XKNX) -> None:
    """Test the event data following the state machine / event octet."""
    conn = await connect(xknx, [None, memory_response(2, 0xB6EB)])
    await dmp_load_state_machine_write_r_co_mem(
        conn,
        ResourceObjectType.OBJECT_ASSOCIATION_TABLE,
        LoadEvent.ADDITIONAL_LOAD_CONTROLS,
        b"\x00\x40\x00",
    )
    assert sent_requests(xknx)[0] == apci.MemoryWrite(
        address=0x0104, data=b"\x23\x00\x40\x00" + bytes(7)
    )


async def test_dmp_load_state_machine_write_r_co_mem_reads_at_most_three_times(
    xknx: XKNX,
) -> None:
    """Test that the state is read at most three times."""
    conn = await connect(
        xknx,
        [
            None,
            memory_response(2, 0xB6EA),
            memory_response(2, 0xB6EA),
            memory_response(2, 0xB6EA),
        ],
    )
    with pytest.raises(VerificationError):
        await dmp_load_state_machine_write_r_co_mem(
            conn, ResourceObjectType.OBJECT_ADDRESS_TABLE, LoadEvent.LOAD_COMPLETED
        )
    requests = sent_requests(xknx)
    assert requests[0].data[0] == 0x12
    assert requests[1:] == [apci.MemoryRead(address=0xB6EA, count=1)] * 3


async def test_dmp_load_state_machine_write_r_co_mem_no_verify(xknx: XKNX) -> None:
    """Test that verify=False reads the state once and returns it."""
    conn = await connect(xknx, [None, memory_response(3)])
    state = await dmp_load_state_machine_write_r_co_mem(
        conn,
        ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
        LoadEvent.LOAD_COMPLETED,
        verify=False,
    )
    assert state is LoadState.ERROR
    assert len(sent_requests(xknx)) == 2


@pytest.mark.parametrize(
    ("state_machine", "event_data"),
    [
        (ResourceObjectType.OBJECT_DEVICE, b""),
        (ResourceObjectType.OBJECT_APPLICATION_PROGRAM, bytes(11)),
    ],
)
async def test_dmp_load_state_machine_write_r_co_mem_invalid(
    xknx: XKNX, state_machine: ResourceObjectType, event_data: bytes
) -> None:
    """Test that an invalid state machine or too long event data is rejected first."""
    conn = await connect(xknx, [])
    with pytest.raises(ValueError):
        await dmp_load_state_machine_write_r_co_mem(
            conn, state_machine, LoadEvent.START_LOADING, event_data
        )
    assert sent_requests(xknx) == []
