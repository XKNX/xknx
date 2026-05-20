"""Legacy wrappers for DM_* procedures — use xknx.management.connection() directly instead."""

from __future__ import annotations

from typing import TYPE_CHECKING
import warnings

from xknx.telegram.address import IndividualAddress, IndividualAddressableType

from .dm_restart_r_co import dm_restart

if TYPE_CHECKING:
    from xknx import XKNX


async def dm_restart_legacy(
    xknx: XKNX,
    individual_address: IndividualAddressableType,
) -> None:
    """Legacy wrapper — open a connection and call dm_restart(conn) instead."""
    warnings.warn(
        "Calling dm_restart(xknx, address) is deprecated."
        " Open a connection with xknx.management.connection(address) and call dm_restart(conn) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    async with xknx.management.connection(
        IndividualAddress(individual_address)
    ) as conn:
        await dm_restart(conn)
