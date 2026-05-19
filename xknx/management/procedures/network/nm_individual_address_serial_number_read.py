"""NM_IndividualAddress_SerialNumber_Read — KNX 03.05.02 §2.4."""

from __future__ import annotations

import logging

from xknx.management.protocols import Broadcaster
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress

logger = logging.getLogger("xknx.management.procedures")


async def nm_individual_address_serial_number_read(
    broadcaster: Broadcaster,
    serial: bytes,
    timeout: float = 3,
) -> IndividualAddress | None:
    """Read individual address from device with specified serial number."""
    async with broadcaster.broadcast() as bc_context:
        await broadcaster.send_broadcast(
            payload=apci.IndividualAddressSerialRead(serial=serial)
        )
        async for result in bc_context.receive(timeout=timeout):
            if (
                isinstance(result.payload, apci.IndividualAddressSerialResponse)
                and result.payload.serial == serial
            ):
                return result.source_address

    return None
