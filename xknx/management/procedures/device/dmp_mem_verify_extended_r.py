"""DMP_MemVerify_Extended_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.23."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from .const import MEMORY_EXTENDED_HEADER_OCTETS, MEMORY_EXTENDED_MAX_COUNT

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
    03.05.02 - §3.23. Requires an established connection (DM_Connect must
    be executed first). Read-only - unlike
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
    if not 0 <= address <= 0xFFFFFF:
        raise ValueError(f"address must be 0-16777215, got {address}")
    if expected_data and address + len(expected_data) - 1 > 0xFFFFFF:
        raise ValueError(
            f"address + len(expected_data) - 1 must be <= 0xffffff, got "
            f"{address + len(expected_data) - 1:#08x}"
        )
    if max_apdu_length <= 0:
        raise ValueError(f"max_apdu_length must be positive, got {max_apdu_length}")
    if not expected_data:
        return

    max_chunk_size = min(
        MEMORY_EXTENDED_MAX_COUNT, max_apdu_length - MEMORY_EXTENDED_HEADER_OCTETS
    )
    if max_chunk_size <= 0:
        raise ValueError(
            f"max_apdu_length {max_apdu_length} leaves no room for memory data "
            f"(header is {MEMORY_EXTENDED_HEADER_OCTETS} octets)"
        )

    offset = 0
    current_address = address

    while offset < len(expected_data):
        expected_chunk = expected_data[offset : offset + max_chunk_size]
        response = await conn.request(
            apci.MemoryExtendedRead(address=current_address, count=len(expected_chunk))
        )
        payload = response.payload
        if payload.return_code != apci.ReturnCode.E_SUCCESS.value:
            raise ManagementConnectionError(
                f"Extended memory verify failed: address {current_address:#08x} "
                f"return code {payload.return_code:#04x}"
            )
        if payload.address != current_address:
            raise ManagementConnectionError(
                f"Extended memory verify failed: requested address "
                f"{current_address:#08x}, response echoed {payload.address:#08x}"
            )
        if len(payload.data) != len(expected_chunk):
            raise ManagementConnectionError(
                f"Extended memory verify failed: address {current_address:#08x} "
                f"requested {len(expected_chunk)} octets, got {len(payload.data)}"
            )
        if payload.data != expected_chunk:
            raise VerificationError(
                f"Extended memory verify mismatch at address "
                f"{current_address:#08x}: expected {expected_chunk.hex()}, "
                f"got {payload.data.hex()}"
            )
        current_address += len(expected_chunk)
        offset += len(expected_chunk)
