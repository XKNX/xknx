"""Tests for device management legacy wrappers."""

from unittest.mock import AsyncMock, patch

import pytest

from xknx import XKNX
from xknx.management.procedures.device.legacy import dm_restart_legacy
from xknx.telegram import IndividualAddress


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_dm_restart_legacy() -> None:
    """Test dm_restart_legacy opens a connection and calls dm_restart."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    address = IndividualAddress("4.0.10")

    with patch(
        "xknx.management.procedures.device.legacy.dm_restart", new_callable=AsyncMock
    ) as mock:
        await dm_restart_legacy(xknx, address)

    mock.assert_awaited_once()
