"""DMP_MemRead_Extended_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.24."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from .const import MEMORY_EXTENDED_HEADER_OCTETS, MEMORY_EXTENDED_MAX_COUNT

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
    - §3.24. Requires an established connection (DM_Connect must be executed
    first). Unlike :func:`~.dmp_mem_read_r_co.dmp_mem_read_r_co`'s
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
        negative return code, echoes a different address than requested, or
        carries fewer octets than requested
    """
    if size < 0:
        raise ValueError(f"size must be >= 0, got {size}")
    if not 0 <= address <= 0xFFFFFF:
        raise ValueError(f"address must be 0-16777215, got {address}")
    if size and address + size - 1 > 0xFFFFFF:
        raise ValueError(
            f"address + size - 1 must be <= 0xffffff, got {address + size - 1:#08x}"
        )
    if max_apdu_length <= 0:
        raise ValueError(f"max_apdu_length must be positive, got {max_apdu_length}")

    max_chunk_size = min(
        MEMORY_EXTENDED_MAX_COUNT, max_apdu_length - MEMORY_EXTENDED_HEADER_OCTETS
    )
    if max_chunk_size <= 0:
        raise ValueError(
            f"max_apdu_length {max_apdu_length} leaves no room for memory data "
            f"(header is {MEMORY_EXTENDED_HEADER_OCTETS} octets)"
        )

    data = bytearray()
    remaining = size
    current_address = address

    while remaining > 0:
        chunk_size = min(remaining, max_chunk_size)
        response = await conn.request(
            apci.MemoryExtendedRead(address=current_address, count=chunk_size)
        )
        payload = response.payload
        if payload.return_code != apci.ReturnCode.E_SUCCESS.value:
            raise ManagementConnectionError(
                f"Extended memory read failed: address {current_address:#08x} "
                f"return code {payload.return_code:#04x}"
            )
        if payload.address != current_address:
            raise ManagementConnectionError(
                f"Extended memory read failed: requested address "
                f"{current_address:#08x}, response echoed {payload.address:#08x}"
            )
        if len(payload.data) != chunk_size:
            raise ManagementConnectionError(
                f"Extended memory read failed: address {current_address:#08x} "
                f"requested {chunk_size} octets, got {len(payload.data)}"
            )
        data.extend(payload.data)
        current_address += chunk_size
        remaining -= chunk_size

    return bytes(data)
