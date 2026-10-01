"""DMP_MemVerify_Extended_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.23."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from ._memory import EXTENDED_MEMORY, is_negative_return_code, memory_chunks

__all__ = ["dmp_mem_verify_extended_r"]


async def dmp_mem_verify_extended_r(
    conn: P2PConnection,
    address: int,
    expected_data: bytes,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> None:
    """
    Verify that a KNX device's extended-addressed memory matches expected data, block by block.

    DMP_MemVerify_Extended_R — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.23. The spec allows the connection-oriented or
    connectionless mode; this implementation uses the connection-oriented
    one - pass an open ``P2PConnection``. Read-only - unlike
    :func:`~.dmp_mem_write_extended_r.dmp_mem_write_extended_r`, does not
    write anything first. The spec notes this produces the same amount of
    bus traffic as a plain write and is only useful against a device with
    no write-time optimization ("writes Data no matter if the same data is
    already stored in the memory").

    :param conn: Active P2P connection to the device
    :param address: Start address in device memory (0-16777215)
    :param expected_data: Data the memory is expected to contain
    :param max_apdu_length: Caps each chunk so its
        A_MemoryExtended_Read_Response-PDU fits within this many octets -
        the device's PID_MAX_APDU_LENGTH (KNX v01.10.01 - Resources
        03.05.01 - §4.3.7). Defaults to the spec's own fallback of 10 octets
        of data for a device that doesn't support L_Data_Extended frames
        (STANDARD_FRAME_MAX_NPDU_LENGTH minus this service's 5 octet
        header); pass the real value for a device known to support more.
    :raises ValueError: If the address range is out of range, or
        max_apdu_length is not positive
    :raises ManagementConnectionError: If a chunk's response carries a
        negative return code, echoes a different address than requested, or
        carries fewer octets than requested
    :raises VerificationError: If a block's data doesn't match expected
    """
    for chunk_address, offset, length in memory_chunks(
        EXTENDED_MEMORY,
        address,
        len(expected_data),
        max_apdu_length,
        size_name="len(expected_data)",
    ):
        expected_chunk = expected_data[offset : offset + length]
        response = await conn.request(
            apci.MemoryExtendedRead(address=chunk_address, count=length)
        )
        payload = response.payload
        if is_negative_return_code(payload.return_code):
            raise ManagementConnectionError(
                f"Extended memory verify failed: address "
                f"{EXTENDED_MEMORY.format_address(chunk_address)} "
                f"return code {payload.return_code:#04x}"
            )
        if payload.address != chunk_address:
            raise ManagementConnectionError(
                f"Extended memory verify failed: requested address "
                f"{EXTENDED_MEMORY.format_address(chunk_address)}, response echoed "
                f"{EXTENDED_MEMORY.format_address(payload.address)}"
            )
        if len(payload.data) != length:
            raise ManagementConnectionError(
                f"Extended memory verify failed: address "
                f"{EXTENDED_MEMORY.format_address(chunk_address)} requested "
                f"{length} octets, got {len(payload.data)}"
            )
        if payload.data != expected_chunk:
            raise VerificationError(
                f"Extended memory verify mismatch at address "
                f"{EXTENDED_MEMORY.format_address(chunk_address)}: "
                f"expected {expected_chunk.hex()}, got {payload.data.hex()}"
            )
