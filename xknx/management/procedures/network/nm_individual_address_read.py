"""NM_IndividualAddress_Read — KNX v02.01.02 - Management Procedures 03.05.02 - §2.2."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.exceptions import ManagementConnectionError
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")


async def nm_individual_address_read(
    xknx: XKNX,
    timeout: float | None = 3,
    raise_if_multiple: bool = False,
) -> list[IndividualAddress]:
    """
    Request individual addresses of all devices that are in programming mode.

    :param xknx: XKNX object
    :param timeout: specifies the timeout in seconds, the KNX specification requires a timeout of 3s
    :param raise_if_multiple: if true, ManagementConnectionError is raised when multiple devices are in programming mode
    :returns: list of individual address of devices in programming mode
    """
    addresses = []
    async for result in xknx.management.request_broadcast(
        apci.IndividualAddressRead(), timeout=timeout
    ):
        addresses.append(result.source_address)
        if raise_if_multiple and (len(addresses) > 1):
            raise ManagementConnectionError(
                "More than one KNX device is in programming mode."
            )
    return addresses
