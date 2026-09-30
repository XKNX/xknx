"""DMP_UserMemRead_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.21.2."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from ._memory import USER_MEMORY, memory_chunks

__all__ = ["dmp_user_mem_read_r_co"]


async def dmp_user_mem_read_r_co(
    conn: P2PConnection,
    address: int,
    size: int,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> bytes:
    """
    Read a contiguous block of extended-range memory from a KNX device.

    DMP_UserMemRead_RCo — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.21.2. Requires an established connection (DM_Connect must be executed
    first). Unlike DMP_MemRead_RCo, addresses the 1 MiB A_UserMemory_*
    address space rather than the 64 KiB A_Memory_* one.

    :param conn: Active P2P connection to the device
    :param address: Start address in device memory (0-0xFFFFF)
    :param size: Number of octets to read
    :param max_apdu_length: Caps each chunk so its A_UserMemory_Response-PDU
        fits within this many octets - the device's PID_MAX_APDU_LENGTH (KNX
        v01.10.01 - Resources 03.05.01 - §4.3.7). Defaults to the spec's
        fallback of 15 octets for a device whose actual value hasn't been
        read; pass the real value for a device known to support more.
    :return: The data read from device memory
    :raises ValueError: If size is negative, the address range is out of
        range, or max_apdu_length is not positive
    :raises ManagementConnectionError: If a chunk's response carries fewer
        octets than requested, or echoes a different address than requested
    """
    data = bytearray()
    for chunk_address, _, chunk_size in memory_chunks(
        USER_MEMORY, address, size, max_apdu_length
    ):
        response = await conn.request(
            apci.UserMemoryRead(address=chunk_address, count=chunk_size)
        )
        if response.payload.address != chunk_address:
            raise ManagementConnectionError(
                f"User memory read failed: requested address "
                f"{USER_MEMORY.format_address(chunk_address)}, response echoed "
                f"{USER_MEMORY.format_address(response.payload.address)}"
            )
        if len(response.payload.data) != chunk_size:
            raise ManagementConnectionError(
                f"User memory read failed: address "
                f"{USER_MEMORY.format_address(chunk_address)} requested "
                f"{chunk_size} octets, got {len(response.payload.data)}"
            )
        data.extend(response.payload.data)

    return bytes(data)
