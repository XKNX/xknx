"""Tests for dmp_load_state_machine_write_r_co_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.3."""

import asyncio
import itertools
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import VerificationError
from xknx.management.procedures.device.dmp_load_state_machine_write_r_co_io import (
    dmp_load_state_machine_write_r_co_io,
    load_event_data_relative_allocation,
    load_event_relative_allocation,
)
from xknx.profile.const import LoadEvent, LoadState
from xknx.telegram import apci

from ....conftest import EventLoopClockAdvancer
from .load_state_machine_helpers import (
    connect,
    property_read,
    property_response,
    property_write,
    sent_requests,
)


@pytest.fixture(name="xknx")
def fixture_xknx() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


async def test_dmp_load_state_machine_write_r_co_io(xknx: XKNX) -> None:
    """Test sending an event: 10 octets of load control, the state is returned."""
    conn = await connect(xknx, [property_response(b"\x02")])
    state = await dmp_load_state_machine_write_r_co_io(conn, 3, LoadEvent.START_LOADING)
    assert state is LoadState.LOADING
    assert sent_requests(xknx) == [
        apci.PropertyValueWrite(
            object_index=3,
            property_id=5,
            count=1,
            start_index=1,
            data=b"\x01" + bytes(9),
        )
    ]


async def test_dmp_load_state_machine_write_r_co_io_property_id(xknx: XKNX) -> None:
    """Test sending an event to another Property and reading it again."""
    conn = await connect(xknx, [property_response(b"\x05"), property_response(b"\x01")])
    await dmp_load_state_machine_write_r_co_io(
        conn, 3, LoadEvent.LOAD_COMPLETED, property_id=60, poll_interval=0
    )
    assert [request.property_id for request in sent_requests(xknx)] == [60, 60]


async def test_dmp_load_state_machine_write_r_co_io_no_verify(xknx: XKNX) -> None:
    """Test that verify=False returns any state."""
    conn = await connect(xknx, [property_response(b"\x03")])
    state = await dmp_load_state_machine_write_r_co_io(
        conn, 3, LoadEvent.LOAD_COMPLETED, verify=False
    )
    assert state is LoadState.ERROR


async def test_dmp_load_state_machine_write_r_co_io_verify_fails(xknx: XKNX) -> None:
    """Test that verify rejects a wrong resulting state."""
    conn = await connect(xknx, [property_response(b"\x03")])
    with pytest.raises(VerificationError, match="ERROR, expected LOADED"):
        await dmp_load_state_machine_write_r_co_io(conn, 3, LoadEvent.LOAD_COMPLETED)


async def test_dmp_load_state_machine_write_r_co_io_event_data(xknx: XKNX) -> None:
    """Test an Additional Load Control with its sub type and data."""
    conn = await connect(xknx, [property_response(b"\x02")])
    await dmp_load_state_machine_write_r_co_io(
        conn, 3, LoadEvent.ADDITIONAL_LOAD_CONTROLS, b"\x0a\x01\x00"
    )
    assert sent_requests(xknx)[0].data == b"\x03\x0a\x01\x00" + bytes(6)


async def test_dmp_load_state_machine_write_r_co_io_event_data_too_long(
    xknx: XKNX,
) -> None:
    """Test that event data longer than 9 octets is rejected before sending."""
    conn = await connect(xknx, [])
    with pytest.raises(ValueError):
        await dmp_load_state_machine_write_r_co_io(
            conn, 3, LoadEvent.ADDITIONAL_LOAD_CONTROLS, bytes(10)
        )
    assert sent_requests(xknx) == []


async def test_dmp_load_state_machine_write_r_co_io_poll_interval_too_long(
    xknx: XKNX,
) -> None:
    """Test that a poll interval longer than 3 seconds is rejected before sending."""
    conn = await connect(xknx, [])
    with pytest.raises(ValueError, match="poll_interval"):
        await dmp_load_state_machine_write_r_co_io(
            conn, 3, LoadEvent.LOAD_COMPLETED, poll_interval=3.5
        )
    assert sent_requests(xknx) == []


async def test_dmp_load_state_machine_write_r_co_io_load_completing(
    xknx: XKNX,
) -> None:
    """Test that the state is read again while it is LoadCompleting."""
    conn = await connect(
        xknx,
        [
            property_response(b"\x05"),
            property_response(b"\x05"),
            property_response(b"\x01"),
        ],
    )
    state = await dmp_load_state_machine_write_r_co_io(
        conn, 3, LoadEvent.LOAD_COMPLETED, poll_interval=0
    )
    assert state is LoadState.LOADED
    assert sent_requests(xknx) == [property_write(0x02)] + [property_read()] * 2


async def test_dmp_load_state_machine_write_r_co_io_unload_intermediate_states(
    xknx: XKNX,
) -> None:
    """Test that Unload waits through LoadCompleting and Unloading."""
    conn = await connect(
        xknx,
        [
            property_response(b"\x05"),
            property_response(b"\x04"),
            property_response(b"\x00"),
        ],
    )
    state = await dmp_load_state_machine_write_r_co_io(
        conn, 3, LoadEvent.UNLOAD, poll_interval=0
    )
    assert state is LoadState.UNLOADED
    assert len(sent_requests(xknx)) == 3


async def test_dmp_load_state_machine_write_r_co_io_event_ignored(
    xknx: XKNX,
) -> None:
    """Test an event ignored while a previous load is still completing."""
    conn = await connect(xknx, [property_response(b"\x05"), property_response(b"\x01")])
    with pytest.raises(VerificationError, match="LOADED, expected LOADING"):
        await dmp_load_state_machine_write_r_co_io(
            conn, 3, LoadEvent.START_LOADING, poll_interval=0
        )
    assert sent_requests(xknx) == [property_write(0x01), property_read()]


async def test_dmp_load_state_machine_write_r_co_io_timeout(
    xknx: XKNX, time_travel: EventLoopClockAdvancer
) -> None:
    """Test that LoadCompleting is read again for 30 seconds before failing."""
    conn = await connect(xknx, itertools.repeat(property_response(b"\x05")))
    task = asyncio.create_task(
        dmp_load_state_machine_write_r_co_io(
            conn, 3, LoadEvent.LOAD_COMPLETED, poll_interval=3
        )
    )
    for _ in range(9):
        await time_travel(3)
    assert not task.done()
    await time_travel(3)
    with pytest.raises(VerificationError, match="after the 30 s timeout"):
        await task
    assert sent_requests(xknx) == [property_write(0x02)] + [property_read()] * 10


def test_load_event_relative_allocation() -> None:
    """Test the event data of a Load Event Relative Allocation."""
    assert load_event_relative_allocation(0x0120) == b"\x0a\x01\x20"
    with pytest.raises(ValueError):
        load_event_relative_allocation(0x10000)
    with pytest.raises(ValueError):
        load_event_relative_allocation(-1)


def test_load_event_data_relative_allocation() -> None:
    """Test the event data of a Load Event Data Relative Allocation."""
    assert (
        load_event_data_relative_allocation(0x00012345)
        == b"\x0b\x00\x01\x23\x45\x00\x00"
    )
    assert (
        load_event_data_relative_allocation(0x00012345, fill=0xFF)
        == b"\x0b\x00\x01\x23\x45\x01\xff"
    )
    with pytest.raises(ValueError):
        load_event_data_relative_allocation(0x100000000)
    with pytest.raises(ValueError):
        load_event_data_relative_allocation(1, fill=0x100)


async def test_dmp_load_state_machine_write_r_co_io_relative_allocation(
    xknx: XKNX,
) -> None:
    """Test sending a Load Event Data Relative Allocation as load control."""
    conn = await connect(xknx, [property_response(b"\x02")])
    await dmp_load_state_machine_write_r_co_io(
        conn,
        3,
        LoadEvent.ADDITIONAL_LOAD_CONTROLS,
        load_event_data_relative_allocation(0x400, fill=0),
    )
    assert sent_requests(xknx)[0].data == (b"\x03\x0b\x00\x00\x04\x00\x01\x00\x00\x00")
