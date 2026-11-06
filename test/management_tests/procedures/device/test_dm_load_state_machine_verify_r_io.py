"""Tests for dm_load_state_machine_verify_r_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.32.3."""

from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import VerificationError
from xknx.management.procedures.device.dm_load_state_machine_verify_r_io import (
    dm_load_state_machine_verify_r_io,
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


async def test_dm_load_state_machine_verify_r_io(xknx: XKNX) -> None:
    """Test verifying the state of a property based Load State Machine."""
    conn = await connect(xknx, [property_response(b"\x01"), property_response(b"\x00")])
    await dm_load_state_machine_verify_r_io(conn, 3, LoadState.LOADED)
    with pytest.raises(VerificationError):
        await dm_load_state_machine_verify_r_io(conn, 3, LoadState.LOADED)
    assert sent_requests(xknx) == [property_read()] * 2


async def test_dm_load_state_machine_verify_r_io_property_id(xknx: XKNX) -> None:
    """Test verifying the state of another Property."""
    conn = await connect(xknx, [property_response(b"\x00")])
    await dm_load_state_machine_verify_r_io(conn, 3, LoadState.UNLOADED, property_id=60)
    assert sent_requests(xknx) == [
        apci.PropertyValueRead(object_index=3, property_id=60, count=1, start_index=1)
    ]
