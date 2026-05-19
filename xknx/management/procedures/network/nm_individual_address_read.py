"""NM_IndividualAddress_Read — KNX 03.05.02 §2.2."""

from __future__ import annotations

import logging

from xknx.exceptions import ManagementConnectionError
from xknx.management.protocols import Broadcaster
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress

logger = logging.getLogger("xknx.management.procedures")


async def nm_individual_address_read(
    broadcaster: Broadcaster,
    timeout: float | None = 3,
    raise_if_multiple: bool = False,
) -> list[IndividualAddress]:
    """
    Request individual addresses of all devices that are in programming mode.

    :param broadcaster: broadcaster for sending and receiving broadcast telegrams
    :param timeout: specifies the timeout in seconds, the KNX specification requires a timeout of 3s
    :param raise_if_multiple: if true, ManagementConnectionError is raised when multiple devices are in programming mode
    :returns: list of individual address of devices in programming mode
    """
    addresses = []
    async with broadcaster.broadcast() as bc_context:
        await broadcaster.send_broadcast(apci.IndividualAddressRead())
        async for result in bc_context.receive(timeout=timeout):
            if isinstance(result.payload, apci.IndividualAddressResponse):
                addresses.append(result.source_address)
                if raise_if_multiple and (len(addresses) > 1):
                    raise ManagementConnectionError(
                        "More than one KNX device is in programming mode."
                    )
    return addresses
