"""DMP_UserMemWrite_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.19.2."""

from __future__ import annotations

import asyncio

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from ._memory import USER_MEMORY, memory_chunks

__all__ = ["dmp_user_mem_write_r_co"]


async def dmp_user_mem_write_r_co(
    conn: P2PConnection,
    address: int,
    data: bytes,
    verify: bool = False,
    write_delay: float = 0,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> None:
    """
    Write a contiguous block of data to extended-range device memory.

    DMP_UserMemWrite_RCo — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.19.2. Requires an established connection (DM_Connect must be executed
    first). Unlike DMP_MemWrite_RCo, addresses the 1 MiB A_UserMemory_*
    address space rather than the 64 KiB A_Memory_* one. The Verify Mode of
    the Management Server shall not be used (see the spec's "Use" clause) -
    ``verify`` here drives the Management Client-side read-back the spec
    describes, not the device's own Verify Mode.

    A_UserMemory_Write is not confirmed at the application layer, so with
    ``verify=False`` the caller is expected to leave ``write_delay`` for the
    device to finish programming the written octets before anything else
    addresses them (KNX Note 14: the delay is device- and size-dependent, see
    KNX v01.10.01 - Resources 03.05.01).

    :param conn: Active P2P connection to the device
    :param address: Start address in device memory (0-0xFFFFF)
    :param data: Data to write
    :param verify: If True, read back and compare each chunk right after
        it is written, instead of waiting out ``write_delay``
    :param write_delay: Delay in seconds after each chunk when
        ``verify=False``. Ignored when ``verify=True``.
    :param max_apdu_length: Caps each chunk so its A_UserMemory_Write-PDU
        fits within this many octets - the device's PID_MAX_APDU_LENGTH (KNX
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
    for chunk_address, offset, length in memory_chunks(
        USER_MEMORY, address, len(data), max_apdu_length, size_name="len(data)"
    ):
        chunk = data[offset : offset + length]
        await conn.send_data(apci.UserMemoryWrite(address=chunk_address, data=chunk))

        if verify:
            response = await conn.request(
                apci.UserMemoryRead(address=chunk_address, count=len(chunk))
            )
            if response.payload.address != chunk_address:
                raise ManagementConnectionError(
                    f"User memory verify failed: requested address "
                    f"{USER_MEMORY.format_address(chunk_address)}, response echoed "
                    f"{USER_MEMORY.format_address(response.payload.address)}"
                )
            if response.payload.data != chunk:
                raise VerificationError(
                    f"User memory verify failed at address "
                    f"{USER_MEMORY.format_address(chunk_address)}: "
                    f"expected {chunk.hex()}, got {response.payload.data.hex()}"
                )
        elif write_delay > 0:
            await asyncio.sleep(write_delay)
