"""Tests for dmp_ext_load_state_machine_verify_r_co_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.32.4."""

from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import VerificationError
from xknx.management.procedures.device.dmp_ext_load_state_machine_verify_r_co_io import (
    dmp_ext_load_state_machine_verify_r_co_io,
)
from xknx.profile.const import LoadState, ResourceObjectType

from .load_state_machine_helpers import connect, ext_response


@pytest.fixture(name="xknx")
def fixture_xknx() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


async def test_dmp_ext_load_state_machine_verify_r_co_io(xknx: XKNX) -> None:
    """Test verifying a Load State Machine with A_FunctionPropertyExtState_Read."""
    conn = await connect(xknx, [ext_response(b"\x00"), ext_response(b"\x01")])
    await dmp_ext_load_state_machine_verify_r_co_io(
        conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, 1, LoadState.UNLOADED
    )
    with pytest.raises(VerificationError):
        await dmp_ext_load_state_machine_verify_r_co_io(
            conn, ResourceObjectType.OBJECT_APPLICATION_PROGRAM, 1, LoadState.UNLOADED
        )
