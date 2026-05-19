"""Tests for network management legacy wrappers."""

from unittest.mock import AsyncMock, patch

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionRefused
from xknx.management.procedures.network.legacy import (
    nm_individual_address_check_legacy,
    nm_individual_address_read_legacy,
    nm_individual_address_serial_number_read_legacy,
    nm_individual_address_serial_number_write_legacy,
    nm_individual_address_write_legacy,
)
from xknx.telegram import IndividualAddress


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_nm_individual_address_check_legacy() -> None:
    """Test nm_individual_address_check_legacy opens a connection and calls nm_individual_address_check."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    address = IndividualAddress("1.1.1")

    with patch(
        "xknx.management.procedures.network.legacy.nm_individual_address_check",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock:
        result = await nm_individual_address_check_legacy(xknx, address)

    mock.assert_awaited_once()
    assert result is True


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_nm_individual_address_check_legacy_refused() -> None:
    """Test nm_individual_address_check_legacy returns True when connection is refused."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    address = IndividualAddress("1.1.1")

    with patch(
        "xknx.management.procedures.network.legacy.nm_individual_address_check",
        new_callable=AsyncMock,
        side_effect=ManagementConnectionRefused("refused"),
    ):
        result = await nm_individual_address_check_legacy(xknx, address)

    assert result is True


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_nm_individual_address_read_legacy() -> None:
    """Test nm_individual_address_read_legacy forwards to nm_individual_address_read."""
    xknx = XKNX()

    with patch(
        "xknx.management.procedures.network.legacy.nm_individual_address_read",
        new_callable=AsyncMock,
        return_value=[],
    ) as mock:
        result = await nm_individual_address_read_legacy(xknx, timeout=5, raise_if_multiple=True)

    mock.assert_awaited_once_with(xknx.management, timeout=5, raise_if_multiple=True)
    assert result == []


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_nm_individual_address_serial_number_read_legacy() -> None:
    """Test nm_individual_address_serial_number_read_legacy forwards correctly."""
    xknx = XKNX()
    serial = b"aabbccddeeff"
    address = IndividualAddress("1.1.5")

    with patch(
        "xknx.management.procedures.network.legacy.nm_individual_address_serial_number_read",
        new_callable=AsyncMock,
        return_value=address,
    ) as mock:
        result = await nm_individual_address_serial_number_read_legacy(xknx, serial=serial, timeout=5)

    mock.assert_awaited_once_with(xknx.management, serial=serial, timeout=5)
    assert result == address


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_nm_individual_address_serial_number_write_legacy() -> None:
    """Test nm_individual_address_serial_number_write_legacy forwards correctly."""
    xknx = XKNX()
    serial = b"aabbccddeeff"
    address = IndividualAddress("1.1.5")

    with patch(
        "xknx.management.procedures.network.legacy.nm_individual_address_serial_number_write",
        new_callable=AsyncMock,
    ) as mock:
        await nm_individual_address_serial_number_write_legacy(xknx, serial=serial, individual_address=address)

    mock.assert_awaited_once_with(xknx.management, serial=serial, individual_address=address)


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_nm_individual_address_write_legacy() -> None:
    """Test nm_individual_address_write_legacy forwards to nm_individual_address_write."""
    xknx = XKNX()
    address = IndividualAddress("1.1.5")

    with patch(
        "xknx.management.procedures.network.legacy.nm_individual_address_write",
        new_callable=AsyncMock,
    ) as mock:
        await nm_individual_address_write_legacy(xknx, address)

    mock.assert_awaited_once_with(xknx.management, xknx.management, address)
