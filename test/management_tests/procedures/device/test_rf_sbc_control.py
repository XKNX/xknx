"""Tests for dm_function_property_write_r (KNX v02.01.02 - Management Procedures 03.05.02 - §3.30) and rf_sbc_control_write."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import Management
from xknx.management.procedures.device import rf_sbc_control
from xknx.management.procedures.device.dm_function_property_write_r import (
    dm_function_property_write_r,
)
from xknx.management.procedures.device.rf_sbc_control import (
    RFSBCMode,
    rf_sbc_control_write,
)
from xknx.telegram import IndividualAddress, Telegram, apci

COUPLER = IndividualAddress("1.2.0")


def _connection(response: apci.APCI) -> AsyncMock:
    """Return a connection answering every request with `response`."""
    conn = AsyncMock()
    conn.request.return_value = Telegram(
        source_address=COUPLER,
        destination_address=IndividualAddress(0),
        payload=response,
    )
    return conn


async def test_function_property_write() -> None:
    """Test the command is sent and the answer returned."""
    response = apci.FunctionPropertyStateResponse(
        object_index=7, property_id=112, return_code=0, data=b"\x02"
    )
    conn = _connection(response)
    assert await dm_function_property_write_r(conn, 7, 112, b"\x02") == response
    conn.request.assert_awaited_once_with(
        apci.FunctionPropertyCommand(object_index=7, property_id=112, data=b"\x02")
    )


@pytest.mark.parametrize(
    "response",
    [
        apci.FunctionPropertyStateResponse(object_index=8, property_id=112),
        apci.FunctionPropertyStateResponse(object_index=7, property_id=113),
        apci.PropertyValueResponse(object_index=7, property_id=112),
    ],
)
async def test_function_property_write_other_answer(response: apci.APCI) -> None:
    """Test an answer for anything else is refused."""
    with pytest.raises(ManagementConnectionError, match="No Function Property"):
        await dm_function_property_write_r(_connection(response), 7, 112, b"\x02")


def _coupler(
    response: apci.APCI, indexes: list[int]
) -> tuple[XKNX, AsyncMock, list[Any]]:
    """Patch the object index read and the connection to a coupler."""
    xknx = XKNX()
    conn = _connection(response)
    reads: list[Any] = []

    async def index_read(*args: Any, **kwargs: Any) -> list[int]:
        reads.append((args[1:], kwargs))
        return indexes

    @asynccontextmanager
    async def connection(
        management: Management, address: IndividualAddress
    ) -> AsyncIterator[AsyncMock]:
        assert address == COUPLER
        yield conn

    patch.object(rf_sbc_control, "nm_object_index_read", index_read).start()
    patch.object(Management, "connection", connection).start()
    return xknx, conn, reads


@pytest.fixture(autouse=True)
def _stop_patches() -> Any:
    """Undo the patches of a test."""
    yield
    patch.stopall()


async def test_rf_sbc_control_write() -> None:
    """Test the mode is written to the RF Router Object."""
    xknx, conn, reads = _coupler(
        apci.FunctionPropertyStateResponse(
            object_index=9, property_id=112, return_code=0, data=b"\x02"
        ),
        [9],
    )
    assert await rf_sbc_control_write(xknx, "1.2.0", RFSBCMode.SYSTEM_BROADCAST) is (
        RFSBCMode.SYSTEM_BROADCAST
    )
    assert reads == [((COUPLER, 6), {"start_instance": 2})]
    conn.request.assert_awaited_once_with(
        apci.FunctionPropertyCommand(object_index=9, property_id=112, data=b"\x02")
    )


async def test_rf_sbc_control_write_without_mode_in_the_answer() -> None:
    """Test an answer without the mode means the one written."""
    xknx, _, _ = _coupler(
        apci.FunctionPropertyStateResponse(object_index=9, property_id=112), [9]
    )
    assert await rf_sbc_control_write(xknx, COUPLER, RFSBCMode.DISABLED) is (
        RFSBCMode.DISABLED
    )


async def test_rf_sbc_control_write_refused() -> None:
    """Test a refused mode and a coupler without RF side."""
    xknx, _, _ = _coupler(
        apci.FunctionPropertyStateResponse(
            object_index=9, property_id=112, return_code=3, data=b"\x00"
        ),
        [9],
    )
    with pytest.raises(ManagementConnectionError, match="return code 3"):
        await rf_sbc_control_write(xknx, COUPLER, RFSBCMode.SYSTEM_BROADCAST)
    patch.stopall()
    xknx, _, _ = _coupler(apci.FunctionPropertyStateResponse(), [])
    with pytest.raises(ManagementConnectionError, match="no Router Object"):
        await rf_sbc_control_write(xknx, COUPLER, RFSBCMode.SYSTEM_BROADCAST)
