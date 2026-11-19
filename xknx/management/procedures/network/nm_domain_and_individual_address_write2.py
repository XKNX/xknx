"""NM_DomainAndIndividualAddress_Write2 — KNX v02.01.02 - Management Procedures 03.05.02 - §2.10."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.exceptions import ManagementConnectionError, ManagementConnectionTimeout
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")


async def nm_domain_and_individual_address_write2(
    xknx: XKNX,
    domain_address: bytes,
    individual_address: IndividualAddressableType,
    *,
    timeout: float | None = 3,
    system_broadcast: bool = True,
) -> IndividualAddress:
    """
    Write the Domain Address and the individual address of the device in programming mode.

    This is the procedure for a KNX RF device - KNX v02.01.01 - Configuration
    Procedures 03.05.03 - §2.3.1.3: the individual address of the single device
    in programming mode is read, its Domain Address written, then its individual
    address when it has another one. The device is verified with a
    connectionless A_DeviceDescriptor_Read at its new address and restarted,
    which ends its programming mode. It is not checked whether another device
    uses the new address.

    The services are sent as system broadcast, which also reaches a device whose
    Domain Address is unknown. With `system_broadcast` false they are broadcasts
    instead, for a device behind a TP1/RF Media Coupler that turns broadcasts
    into system broadcasts (§2.3.1.4). The answer to the verification has the new
    Domain Address: the sender has to receive it, e.g. a KNX RF USB interface with
    the same Domain Address.

    Returns the individual address the device had before. Raises
    ManagementConnectionError when no device or more than one device is in
    programming mode (`timeout` seconds are waited for answers), or when no
    device answers at the new address.

    :param xknx: the XKNX object
    :param domain_address: the new Domain Address, 6 octets on KNX RF
    :param individual_address: the new individual address
    :param timeout: seconds to wait for the devices in programming mode
    :param system_broadcast: send the broadcast services as system broadcast
    """
    new_address = IndividualAddress(individual_address)
    current: list[IndividualAddress] = []
    async for result in xknx.management.broadcast.request(
        apci.IndividualAddressRead(), timeout=timeout, system_broadcast=system_broadcast
    ):
        current.append(result.source_address)
    if not current:
        raise ManagementConnectionError("No device in programming mode detected.")
    if len(current) > 1:
        raise ManagementConnectionError(
            "More than one KNX device is in programming mode."
        )

    await xknx.management.broadcast.send(
        apci.DomainAddressWrite(domain_address=domain_address),
        system_broadcast=system_broadcast,
    )
    logger.debug(
        "Wrote Domain Address %s to device %s.", domain_address.hex(), current[0]
    )
    if new_address != current[0]:
        await xknx.management.broadcast.send(
            apci.IndividualAddressWrite(address=new_address),
            system_broadcast=system_broadcast,
        )
        logger.debug("Wrote individual address %s to device.", new_address)

    async with xknx.management.connectionless(new_address) as connectionless:
        try:
            await connectionless.request(apci.DeviceDescriptorRead(descriptor=0))
        except ManagementConnectionTimeout as exc:
            raise ManagementConnectionError(
                f"No device answered at {new_address} after the address write."
            ) from exc
        logger.debug("Restarting device %s, exiting programming mode.", new_address)
        await connectionless.send(apci.Restart())
    return current[0]
