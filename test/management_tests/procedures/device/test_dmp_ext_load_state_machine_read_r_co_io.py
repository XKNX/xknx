"""Tests for dmp_ext_load_state_machine_read_r_co_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.33.4."""

from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_ext_load_state_machine_read_r_co_io import (
    dmp_ext_load_state_machine_read_r_co_io,
)
from xknx.profile.const import LoadState, ResourceObjectType
from xknx.telegram import apci

from .load_state_machine_helpers import (
    PID_LOAD_STATE_CONTROL,
    connect,
    ext_response,
    property_response,
    sent_requests,
)


@pytest.fixture(name="xknx")
def fixture_xknx() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


async def test_dmp_ext_load_state_machine_read_r_co_io(xknx: XKNX) -> None:
    """Test reading a Load State Machine with A_FunctionPropertyExtState_Read."""
    conn = await connect(xknx, [ext_response(b"\x01")])
    state = await dmp_ext_load_state_machine_read_r_co_io(
        conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, 1
    )
    assert state is LoadState.LOADED
    assert sent_requests(xknx) == [
        apci.FunctionPropertyExtStateRead(
            interface_object_type=ResourceObjectType.OBJECT_APPLICATION_PROGRAM,
            object_instance=1,
            property_id=PID_LOAD_STATE_CONTROL,
        )
    ]


@pytest.mark.parametrize(
    "response",
    [
        ext_response(b"", apci.ReturnCode.E_COMMAND_INVALID),
        ext_response(b""),
        ext_response(b"\x07"),
    ],
)
async def test_dmp_ext_load_state_machine_read_r_co_io_errors(
    xknx: XKNX, response: apci.FunctionPropertyExtStateResponse
) -> None:
    """Test a negative return code, no data and an unknown state."""
    conn = await connect(xknx, [response])
    with pytest.raises(ManagementConnectionError):
        await dmp_ext_load_state_machine_read_r_co_io(
            conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, 1
        )


async def test_dmp_ext_load_state_machine_read_r_co_io_unexpected_response(
    xknx: XKNX,
) -> None:
    """Test that another response than A_FunctionPropertyExtState_Response fails."""
    conn = await connect(xknx, [property_response(b"\x01")])
    with pytest.raises(ManagementConnectionError):
        await dmp_ext_load_state_machine_read_r_co_io(
            conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, 1
        )
