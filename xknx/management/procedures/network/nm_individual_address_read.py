"""NM_IndividualAddress_Read — KNX 03.05.02 §2.2."""

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
    # initialize queue or event handler gathering broadcasts
    async with xknx.management.broadcast() as bc_context:
        await xknx.management.send_broadcast(apci.IndividualAddressRead())
        async for result in bc_context.receive(timeout=timeout):
            if isinstance(result.payload, apci.IndividualAddressResponse):
                addresses.append(result.source_address)
                if raise_if_multiple and (len(addresses) > 1):
                    raise ManagementConnectionError(
                        "More than one KNX device is in programming mode."
                    )
    return addresses
