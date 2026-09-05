"""DMP_MemRead_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.18.2."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from .const import MEMORY_HEADER_OCTETS, MEMORY_MAX_COUNT

__all__ = ["dmp_mem_read_r_co"]


async def dmp_mem_read_r_co(
    conn: P2PConnection,
    address: int,
    size: int,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> bytes:
    """
    Read a contiguous block of memory from a KNX device.

    DMP_MemRead_RCo — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.18.2. Requires an established connection (DM_Connect must be executed
    first).

    :param conn: Active P2P connection to the device
    :param address: Start address in device memory (0-65535)
    :param size: Number of octets to read
    :param max_apdu_length: Caps each chunk so its A_Memory_Response-PDU fits
        within this many octets - the device's PID_MAX_APDU_LENGTH (KNX
        v01.10.01 - Resources 03.05.01 - §4.3.7). Defaults to the spec's
        fallback of 15 octets for a device whose actual value hasn't been
        read; pass the real value for a device known to support more.
    :return: The data read from device memory
    :raises ValueError: If size is negative, the address range is out of
        range, or max_apdu_length is not positive
    :raises ManagementConnectionError: If a chunk's response carries fewer
        octets than requested, or echoes a different address than requested
    """
    if size < 0:
        raise ValueError(f"size must be >= 0, got {size}")
    if not 0 <= address <= 0xFFFF:
        raise ValueError(f"address must be 0-65535, got {address}")
    if size and address + size - 1 > 0xFFFF:
        raise ValueError(
            f"address + size - 1 must be <= 0xffff, got {address + size - 1:#06x}"
        )
    if max_apdu_length <= 0:
        raise ValueError(f"max_apdu_length must be positive, got {max_apdu_length}")

    max_chunk_size = min(MEMORY_MAX_COUNT, max_apdu_length - MEMORY_HEADER_OCTETS)
    if max_chunk_size <= 0:
        raise ValueError(
            f"max_apdu_length {max_apdu_length} leaves no room for memory data "
            f"(header is {MEMORY_HEADER_OCTETS} octets)"
        )

    data = bytearray()
    remaining = size
    current_address = address

    while remaining > 0:
        chunk_size = min(remaining, max_chunk_size)
        response = await conn.request(
            apci.MemoryRead(address=current_address, count=chunk_size)
        )
        if response.payload.address != current_address:
            raise ManagementConnectionError(
                f"Memory read failed: requested address {current_address:#06x}, "
                f"response echoed {response.payload.address:#06x}"
            )
        if len(response.payload.data) != chunk_size:
            raise ManagementConnectionError(
                f"Memory read failed: address {current_address:#06x} requested "
                f"{chunk_size} octets, got {len(response.payload.data)}"
            )
        data.extend(response.payload.data)
        current_address += chunk_size
        remaining -= chunk_size

    return bytes(data)
