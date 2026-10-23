"""Tests for dm_load_state_machine_verify_r_co_mem — KNX v02.01.02 - Management Procedures 03.05.02 - §3.32.2."""

from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import VerificationError
from xknx.management.procedures.device.dm_load_state_machine_verify_r_co_mem import (
    dm_load_state_machine_verify_r_co_mem,
)
from xknx.profile.const import LoadState, ResourceObjectType

from .load_state_machine_helpers import connect, memory_response


@pytest.fixture(name="xknx")
def fixture_xknx() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


async def test_dm_load_state_machine_verify_r_co_mem(xknx: XKNX) -> None:
    """Test verifying a memory mapped Load State Machine."""
    conn = await connect(xknx, [memory_response(1), memory_response(2)])
    await dm_load_state_machine_verify_r_co_mem(
        conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, LoadState.LOADED
    )
    with pytest.raises(VerificationError):
        await dm_load_state_machine_verify_r_co_mem(
            conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, LoadState.LOADED
        )
