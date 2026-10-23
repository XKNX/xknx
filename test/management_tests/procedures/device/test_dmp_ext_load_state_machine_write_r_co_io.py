"""Tests for dmp_ext_load_state_machine_write_r_co_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.5."""

from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.procedures.device.dmp_ext_load_state_machine_write_r_co_io import (
    dmp_ext_load_state_machine_write_r_co_io,
)
from xknx.profile.const import LoadEvent, LoadState, ResourceObjectType
from xknx.telegram import apci

from .load_state_machine_helpers import (
    PID_LOAD_STATE_CONTROL,
    connect,
    ext_response,
    property_response,
    sent_requests,
)

EXT_STATE_READ = apci.FunctionPropertyExtStateRead(
    interface_object_type=ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
    object_instance=1,
    property_id=PID_LOAD_STATE_CONTROL,
)


def _ext_command(data: bytes) -> apci.FunctionPropertyExtCommand:
    return apci.FunctionPropertyExtCommand(
        interface_object_type=ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
        object_instance=1,
        property_id=PID_LOAD_STATE_CONTROL,
        data=data,
    )


@pytest.fixture(name="xknx")
def fixture_xknx() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


async def test_dmp_ext_load_state_machine_write_r_co_io(xknx: XKNX) -> None:
    """Test sending an event with A_FunctionPropertyExtCommand."""
    conn = await connect(xknx, [ext_response(b"\x00")])
    state = await dmp_ext_load_state_machine_write_r_co_io(
        conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, 1, LoadEvent.UNLOAD
    )
    assert state is LoadState.UNLOADED
    assert sent_requests(xknx) == [_ext_command(b"\x04" + bytes(9))]


async def test_dmp_ext_load_state_machine_write_r_co_io_unexpected_response(
    xknx: XKNX,
) -> None:
    """Test that a response of another service raises."""
    conn = await connect(xknx, [property_response(b"\x02")])
    with pytest.raises(ManagementConnectionError, match="unexpected response"):
        await dmp_ext_load_state_machine_write_r_co_io(
            conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, 1, LoadEvent.UNLOAD
        )


async def test_dmp_ext_load_state_machine_write_r_co_io_load_completing(
    xknx: XKNX,
) -> None:
    """Test that LoadCompleting is read again with A_FunctionPropertyExtState_Read."""
    conn = await connect(
        xknx,
        [ext_response(b"\x05"), ext_response(b"\x05"), ext_response(b"\x01")],
    )
    state = await dmp_ext_load_state_machine_write_r_co_io(
        conn,
        ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
        1,
        LoadEvent.LOAD_COMPLETED,
        poll_interval=0,
    )
    assert state is LoadState.LOADED
    assert sent_requests(xknx) == [
        _ext_command(b"\x02" + bytes(9)),
        EXT_STATE_READ,
        EXT_STATE_READ,
    ]


async def test_dmp_ext_load_state_machine_write_r_co_io_verify(xknx: XKNX) -> None:
    """Test that verify is the default and rejects a wrong resulting state."""
    conn = await connect(xknx, [ext_response(b"\x03"), ext_response(b"\x03")])
    with pytest.raises(VerificationError):
        await dmp_ext_load_state_machine_write_r_co_io(
            conn,
            ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
            1,
            LoadEvent.START_LOADING,
        )
    state = await dmp_ext_load_state_machine_write_r_co_io(
        conn,
        ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
        1,
        LoadEvent.START_LOADING,
        verify=False,
    )
    assert state is LoadState.ERROR


async def test_dmp_ext_load_state_machine_write_r_co_io_poll_interval_too_long(
    xknx: XKNX,
) -> None:
    """Test that a poll interval longer than 3 seconds is rejected before sending."""
    conn = await connect(xknx, [])
    with pytest.raises(ValueError, match="poll_interval"):
        await dmp_ext_load_state_machine_write_r_co_io(
            conn,
            ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
            1,
            LoadEvent.LOAD_COMPLETED,
            poll_interval=4,
        )
    assert sent_requests(xknx) == []
