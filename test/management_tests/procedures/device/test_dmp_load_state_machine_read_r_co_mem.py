"""Tests for dmp_load_state_machine_read_r_co_mem — KNX v02.01.02 - Management Procedures 03.05.02 - §3.33.2."""

from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.management.procedures.device.dmp_load_state_machine_read_r_co_mem import (
    dmp_load_state_machine_read_r_co_mem,
)
from xknx.profile.const import LoadState, ResourceObjectType
from xknx.telegram import apci

from .load_state_machine_helpers import connect, memory_response, sent_requests


@pytest.fixture(name="xknx")
def fixture_xknx() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


@pytest.mark.parametrize(
    ("state_machine", "address"),
    [
        (ResourceObjectType.OBJECT_ADDRESS_TABLE, 0xB6EA),
        (ResourceObjectType.OBJECT_ASSOCIATION_TABLE, 0xB6EB),
        (ResourceObjectType.OBJECT_APPLICATION_PROGRAM, 0xB6EC),
        (ResourceObjectType.OBJECT_INTERFACE_PROGRAM, 0xB6ED),
    ],
)
async def test_dmp_load_state_machine_read_r_co_mem(
    xknx: XKNX, state_machine: ResourceObjectType, address: int
) -> None:
    """Test reading a memory mapped Load State Machine of a BIM M112."""
    conn = await connect(xknx, [memory_response(1, address)])
    state = await dmp_load_state_machine_read_r_co_mem(conn, state_machine)
    assert state is LoadState.LOADED
    assert sent_requests(xknx) == [apci.MemoryRead(address=address, count=1)]


async def test_dmp_load_state_machine_read_r_co_mem_invalid_state_machine(
    xknx: XKNX,
) -> None:
    """Test that only the four memory mapped state machine types are accepted."""
    conn = await connect(xknx, [])
    with pytest.raises(ValueError):
        await dmp_load_state_machine_read_r_co_mem(
            conn, ResourceObjectType.OBJECT_DEVICE
        )
    assert sent_requests(xknx) == []
