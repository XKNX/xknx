"""NM_IndividualAddress_SerialNumber_Read — KNX v02.01.02 - Management Procedures 03.05.02 - §2.4."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")


async def nm_individual_address_serial_number_read(
    xknx: XKNX,
    serial: bytes,
    timeout: float = 3,
) -> IndividualAddress | None:
    """Read individual address from device with specified serial number."""
    async for result in xknx.management.request_broadcast(
        apci.IndividualAddressSerialRead(serial=serial), timeout=timeout
    ):
        if result.payload.serial == serial:
            return result.source_address

    return None
