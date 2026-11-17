"""Tests for dmp_load_state_machine_read_r_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.33.3."""

from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_load_state_machine_read_r_io import (
    dmp_load_state_machine_read_r_io,
)
from xknx.profile.const import LoadState
from xknx.telegram import apci

from .load_state_machine_helpers import (
    connect,
    property_read,
    property_response,
    sent_requests,
)


@pytest.fixture(name="xknx")
def fixture_xknx() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


async def test_dmp_load_state_machine_read_r_io(xknx: XKNX) -> None:
    """Test reading the state of a property based Load State Machine."""
    conn = await connect(xknx, [property_response(b"\x01")])
    assert await dmp_load_state_machine_read_r_io(conn, 3) is LoadState.LOADED
    assert sent_requests(xknx) == [property_read()]


async def test_dmp_load_state_machine_read_r_io_property_id(xknx: XKNX) -> None:
    """Test reading the state from another Property."""
    conn = await connect(xknx, [property_response(b"\x02")])
    state = await dmp_load_state_machine_read_r_io(conn, 3, property_id=60)
    assert state is LoadState.LOADING
    assert sent_requests(xknx) == [
        apci.PropertyValueRead(object_index=3, property_id=60, count=1, start_index=1)
    ]


@pytest.mark.parametrize(
    "response", [property_response(b"", count=0), property_response(b"\x07")]
)
async def test_dmp_load_state_machine_read_r_io_errors(
    xknx: XKNX, response: apci.PropertyValueResponse
) -> None:
    """Test a missing Property and an unknown state."""
    conn = await connect(xknx, [response])
    with pytest.raises(ManagementConnectionError):
        await dmp_load_state_machine_read_r_io(conn, 3)
