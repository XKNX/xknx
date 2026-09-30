"""DMP_MemWrite_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.16.2."""

from __future__ import annotations

import asyncio

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from .const import MEMORY_HEADER_OCTETS, MEMORY_MAX_COUNT

__all__ = ["dmp_mem_write_r_co"]


async def dmp_mem_write_r_co(
    conn: P2PConnection,
    address: int,
    data: bytes,
    verify: bool = False,
    write_delay: float = 0,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> None:
    """
    Write a contiguous block of data to device memory.

    DMP_MemWrite_RCo — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.16.2. Requires an established connection (DM_Connect must be executed
    first). The Verify Mode of the Management Server shall not be used (see
    the spec's "Use" clause) - ``verify`` here drives the Management
    Client-side read-back the spec describes, not the device's own Verify
    Mode.

    A_Memory_Write is not confirmed at the application layer, so with
    ``verify=False`` the caller is expected to leave ``write_delay`` for the
    device to finish programming the written octets before anything else
    addresses them (KNX Note 12: the delay is device- and size-dependent, see
    KNX v01.10.01 - Resources 03.05.01).

    :param conn: Active P2P connection to the device
    :param address: Start address in device memory (0-65535)
    :param data: Data to write
    :param verify: If True, read back and compare each chunk right after
        it is written, instead of waiting out ``write_delay``
    :param write_delay: Delay in seconds after each chunk when
        ``verify=False``. Ignored when ``verify=True``.
    :param max_apdu_length: Caps each chunk so its A_Memory_Write-PDU fits
        within this many octets - the device's PID_MAX_APDU_LENGTH (KNX
        v01.10.01 - Resources 03.05.01 - §4.3.7). Defaults to the spec's
        fallback of 15 octets for a device whose actual value hasn't been
        read; pass the real value for a device known to support more.
    :raises ValueError: If address is out of range, the address range is out
        of range, or max_apdu_length is not positive
    :raises ManagementConnectionError: If verify is enabled and the read-back
        echoes a different address than requested
    :raises VerificationError: If verify is enabled and the read-back does
        not match what was written
    """
    if not 0 <= address <= 0xFFFF:
        raise ValueError(f"address must be 0-65535, got {address}")
    if data and address + len(data) - 1 > 0xFFFF:
        raise ValueError(
            f"address + len(data) - 1 must be <= 0xffff, got "
            f"{address + len(data) - 1:#06x}"
        )
    if max_apdu_length <= 0:
        raise ValueError(f"max_apdu_length must be positive, got {max_apdu_length}")
    if not data:
        return

    max_chunk_size = min(MEMORY_MAX_COUNT, max_apdu_length - MEMORY_HEADER_OCTETS)
    if max_chunk_size <= 0:
        raise ValueError(
            f"max_apdu_length {max_apdu_length} leaves no room for memory data "
            f"(header is {MEMORY_HEADER_OCTETS} octets)"
        )

    offset = 0
    current_address = address

    while offset < len(data):
        chunk = data[offset : offset + max_chunk_size]
        await conn.send_data(apci.MemoryWrite(address=current_address, data=chunk))

        if verify:
            response = await conn.request(
                apci.MemoryRead(address=current_address, count=len(chunk))
            )
            if response.payload.address != current_address:
                raise ManagementConnectionError(
                    f"Memory verify failed: requested address "
                    f"{current_address:#06x}, response echoed "
                    f"{response.payload.address:#06x}"
                )
            if response.payload.data != chunk:
                raise VerificationError(
                    f"Memory verify failed at address {current_address:#06x}: "
                    f"expected {chunk.hex()}, got {response.payload.data.hex()}"
                )
        elif write_delay > 0:
            await asyncio.sleep(write_delay)

        current_address += len(chunk)
        offset += len(chunk)
