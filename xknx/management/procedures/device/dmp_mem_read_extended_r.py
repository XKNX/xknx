"""DMP_MemRead_Extended_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.24."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from ._memory import EXTENDED_MEMORY, is_negative_return_code, memory_chunks

__all__ = ["dmp_mem_read_extended_r"]


async def dmp_mem_read_extended_r(
    conn: P2PConnection,
    address: int,
    size: int,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> bytes:
    """
    Read a contiguous block of memory from a KNX device's 16 MiB extended address space.

    DMP_MemRead_Extended_R — KNX v02.01.02 - Management Procedures 03.05.02
    - §3.24. The spec allows the connection-oriented or connectionless mode;
    this implementation uses the connection-oriented one - pass an open
    ``P2PConnection``. Unlike :func:`~.dmp_mem_read_r_co.dmp_mem_read_r_co`'s
    ``A_Memory_Read`` (16 bit address, no confirmed error indication),
    ``A_MemoryExtended_Read`` (KNX v02.01.01 - Application Layer 03.03.07 -
    §3.4.9.1) addresses the full 24 bit space and returns an explicit
    ``return_code`` in every response.

    :param conn: Active P2P connection to the device
    :param address: Start address in device memory (0-16777215)
    :param size: Number of octets to read
    :param max_apdu_length: Caps each chunk so its
        A_MemoryExtended_Read_Response-PDU fits within this many octets -
        the device's PID_MAX_APDU_LENGTH (KNX v01.10.01 - Resources
        03.05.01 - §4.3.7). Defaults to the spec's own fallback of 10 octets
        of data for a device that doesn't support L_Data_Extended frames
        (STANDARD_FRAME_MAX_NPDU_LENGTH minus this service's 5 octet
        header); pass the real value for a device known to support more.
    :return: The data read from device memory
    :raises ValueError: If size is negative, the address range is out of
        range, or max_apdu_length is not positive
    :raises ManagementConnectionError: If a chunk's response carries a
        negative return code (A0h-FFh), echoes a different address than requested, or
        carries fewer octets than requested
    """
    data = bytearray()
    for chunk_address, _, chunk_size in memory_chunks(
        EXTENDED_MEMORY, address, size, max_apdu_length
    ):
        response = await conn.request(
            apci.MemoryExtendedRead(address=chunk_address, count=chunk_size)
        )
        payload = response.payload
        if is_negative_return_code(payload.return_code):
            raise ManagementConnectionError(
                f"Extended memory read failed: address "
                f"{EXTENDED_MEMORY.format_address(chunk_address)} "
                f"return code {payload.return_code:#04x}"
            )
        if payload.address != chunk_address:
            raise ManagementConnectionError(
                f"Extended memory read failed: requested address "
                f"{EXTENDED_MEMORY.format_address(chunk_address)}, response echoed "
                f"{EXTENDED_MEMORY.format_address(payload.address)}"
            )
        if len(payload.data) != chunk_size:
            raise ManagementConnectionError(
                f"Extended memory read failed: address "
                f"{EXTENDED_MEMORY.format_address(chunk_address)} requested "
                f"{chunk_size} octets, got {len(payload.data)}"
            )
        data.extend(payload.data)

    return bytes(data)
