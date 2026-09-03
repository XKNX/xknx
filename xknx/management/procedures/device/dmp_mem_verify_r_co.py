"""DMP_MemVerify_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.17.2."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from .const import MEMORY_HEADER_OCTETS, MEMORY_MAX_COUNT

__all__ = ["dmp_mem_verify_r_co"]


async def dmp_mem_verify_r_co(
    conn: P2PConnection,
    address: int,
    expected_data: bytes,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> None:
    """
    Verify that device memory matches expected data, block by block.

    DMP_MemVerify_RCo — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.17.2. Requires an established connection (DM_Connect must be executed
    first). Read-only - unlike DMP_MemWrite_RCo's own optional verify, this
    does not write anything first.

    :param conn: Active P2P connection to the device
    :param address: Start address in device memory (0-65535)
    :param expected_data: Data the memory is expected to contain
    :param max_apdu_length: Caps each chunk so its A_Memory_Response-PDU fits
        within this many octets - the device's PID_MAX_APDU_LENGTH (KNX
        v01.10.01 - Resources 03.05.01 - §4.3.7). Defaults to the spec's
        fallback of 15 octets for a device whose actual value hasn't been
        read; pass the real value for a device known to support more.
    :raises ValueError: If address is out of range or max_apdu_length is not
        positive
    :raises ManagementConnectionError: If a block's data doesn't match
        expected, or a chunk's response carries fewer octets than requested
    """
    if not 0 <= address <= 0xFFFF:
        raise ValueError(f"address must be 0-65535, got {address}")
    if max_apdu_length <= 0:
        raise ValueError(f"max_apdu_length must be positive, got {max_apdu_length}")
    if not expected_data:
        return

    max_chunk_size = min(MEMORY_MAX_COUNT, max_apdu_length - MEMORY_HEADER_OCTETS)
    if max_chunk_size <= 0:
        raise ValueError(
            f"max_apdu_length {max_apdu_length} leaves no room for memory data "
            f"(header is {MEMORY_HEADER_OCTETS} octets)"
        )

    offset = 0
    current_address = address

    while offset < len(expected_data):
        expected_chunk = expected_data[offset : offset + max_chunk_size]
        response = await conn.request(
            apci.MemoryRead(address=current_address, count=len(expected_chunk))
        )
        if len(response.payload.data) != len(expected_chunk):
            raise ManagementConnectionError(
                f"Memory verify failed: address {current_address:#06x} requested "
                f"{len(expected_chunk)} octets, got {len(response.payload.data)}"
            )
        if response.payload.data != expected_chunk:
            raise ManagementConnectionError(
                f"Memory verify mismatch at address {current_address:#06x}: "
                f"expected {expected_chunk.hex()}, got {response.payload.data.hex()}"
            )
        current_address += len(expected_chunk)
        offset += len(expected_chunk)
