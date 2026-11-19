"""NM_DomainAddress_Read — KNX v02.01.02 - Management Procedures 03.05.02 - §2.7."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")


async def nm_domain_address_read(
    xknx: XKNX,
    timeout: float | None = 3,
    *,
    system_broadcast: bool = True,
) -> list[tuple[IndividualAddress, bytes]]:
    """
    Read the Domain Addresses of all devices in programming mode.

    Every device that answers within `timeout` is returned with its individual
    address and its Domain Address (2 octets on KNX PL110, 6 on KNX RF).

    The request is a system broadcast, so it also reaches a device whose Domain
    Address is not the one of the sender - KNX v02.01.01 - Configuration
    Procedures 03.05.03 - §2.3.1.1. With `system_broadcast` false it is a
    broadcast instead, e.g. for a device behind a TP1/RF Media Coupler that turns
    broadcasts into system broadcasts (§2.3.1.4).

    :param xknx: the XKNX object
    :param timeout: seconds to collect answers, 3 s in the specification
    :param system_broadcast: send the request as system broadcast
    """
    devices: list[tuple[IndividualAddress, bytes]] = []
    async for result in xknx.management.broadcast.request(
        apci.DomainAddressRead(), timeout=timeout, system_broadcast=system_broadcast
    ):
        devices.append((result.source_address, result.payload.domain_address))
    logger.debug("Devices in programming mode: %s", devices)
    return devices
