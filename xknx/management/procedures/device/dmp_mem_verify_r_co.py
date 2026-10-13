"""DMP_MemVerify_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.17.2."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from ._memory import MEMORY, memory_chunks

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
    :raises ValueError: If address is out of range, the address range is out
        of range, or max_apdu_length is not positive
    :raises ManagementConnectionError: If a chunk's response carries fewer
        octets than requested, or echoes a different address than requested
    :raises VerificationError: If a block's data doesn't match expected
    """
    for chunk_address, offset, length in memory_chunks(
        MEMORY,
        address,
        len(expected_data),
        max_apdu_length,
        size_name="len(expected_data)",
    ):
        expected_chunk = expected_data[offset : offset + length]
        response = await conn.request(
            apci.MemoryRead(address=chunk_address, count=length)
        )
        payload = response.payload
        if payload.address != chunk_address:
            raise ManagementConnectionError(
                f"Memory verify failed: requested address "
                f"{MEMORY.format_address(chunk_address)}, response echoed "
                f"{MEMORY.format_address(payload.address)}"
            )
        if len(payload.data) != length:
            raise ManagementConnectionError(
                f"Memory verify failed: address "
                f"{MEMORY.format_address(chunk_address)} requested "
                f"{length} octets, got {len(payload.data)}"
            )
        if payload.data != expected_chunk:
            raise VerificationError(
                f"Memory verify mismatch at address "
                f"{MEMORY.format_address(chunk_address)}: "
                f"expected {expected_chunk.hex()}, got {payload.data.hex()}"
            )
