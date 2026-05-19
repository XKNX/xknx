"""Legacy wrappers for NM_* procedures — pass xknx.management as a ConnectionManager or Broadcaster instead."""

from __future__ import annotations

from typing import TYPE_CHECKING
import warnings

from xknx.exceptions import ManagementConnectionRefused
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

from .nm_individual_address_check import nm_individual_address_check
from .nm_individual_address_read import nm_individual_address_read
from .nm_individual_address_serial_number_read import (
    nm_individual_address_serial_number_read,
)
from .nm_individual_address_serial_number_write import (
    nm_individual_address_serial_number_write,
)
from .nm_individual_address_write import nm_individual_address_write

if TYPE_CHECKING:
    from xknx import XKNX


async def nm_individual_address_check_legacy(
    xknx: XKNX,
    individual_address: IndividualAddressableType,
) -> bool:
    """Legacy wrapper — open a connection and call nm_individual_address_check(conn) instead."""
    warnings.warn(
        "Calling nm_individual_address_check(xknx, address) is deprecated."
        " Open a connection with xknx.management.connection(address) and call nm_individual_address_check(conn) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    try:
        async with xknx.management.connection(
            IndividualAddress(individual_address)
        ) as conn:
            return await nm_individual_address_check(conn)
    except ManagementConnectionRefused:
        return True


async def nm_individual_address_read_legacy(
    xknx: XKNX,
    timeout: float | None = 3,
    raise_if_multiple: bool = False,
) -> list[IndividualAddress]:
    """Legacy wrapper — pass xknx.management and call nm_individual_address_read(broadcaster, ...) instead."""
    warnings.warn(
        "Calling nm_individual_address_read(xknx, ...) is deprecated."
        " Pass xknx.management as the first argument instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return await nm_individual_address_read(
        xknx.management, timeout=timeout, raise_if_multiple=raise_if_multiple
    )


async def nm_individual_address_serial_number_read_legacy(
    xknx: XKNX,
    serial: bytes,
    timeout: float = 3,
) -> IndividualAddress | None:
    """Legacy wrapper — pass xknx.management and call nm_individual_address_serial_number_read(broadcaster, ...) instead."""
    warnings.warn(
        "Calling nm_individual_address_serial_number_read(xknx, ...) is deprecated."
        " Pass xknx.management as the first argument instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return await nm_individual_address_serial_number_read(
        xknx.management, serial=serial, timeout=timeout
    )


async def nm_individual_address_serial_number_write_legacy(
    xknx: XKNX,
    serial: bytes,
    individual_address: IndividualAddressableType,
) -> None:
    """Legacy wrapper — pass xknx.management and call nm_individual_address_serial_number_write(broadcaster, ...) instead."""
    warnings.warn(
        "Calling nm_individual_address_serial_number_write(xknx, ...) is deprecated."
        " Pass xknx.management as the first argument instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    await nm_individual_address_serial_number_write(
        xknx.management, serial=serial, individual_address=individual_address
    )


async def nm_individual_address_write_legacy(
    xknx: XKNX,
    individual_address: IndividualAddressableType,
) -> None:
    """Legacy wrapper — pass xknx.management as both manager and broadcaster instead."""
    warnings.warn(
        "Calling nm_individual_address_write(xknx, address) is deprecated."
        " Pass xknx.management as the first two arguments instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    await nm_individual_address_write(
        xknx.management, xknx.management, individual_address
    )
