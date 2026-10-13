"""DMP_MemWrite_Extended_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.22."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from ._memory import (
    EXTENDED_MEMORY,
    is_negative_return_code,
    memory_chunks,
    memory_extended_write_crc,
)

__all__ = ["dmp_mem_write_extended_r"]

# KNX v02.01.01 - Application Layer 03.03.07 - §3.4.9.2.1, Table 4 "Write
# Return Codes": 01h is a second positive code specific to
# A_MemoryExtended_Write_Response ("CRC over original data") - a device may
# confirm a write with a CRC16-CCITT instead of a bare E_SUCCESS, at its own
# discretion (footnote 12). The CRC is checked when it's sent.
_E_SUCCESS_WITH_CRC = 0x01


async def dmp_mem_write_extended_r(
    conn: P2PConnection,
    address: int,
    data: bytes,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> None:
    """
    Write a contiguous block of data to a KNX device's 16 MiB extended address space.

    DMP_MemWrite_Extended_R — KNX v02.01.02 - Management Procedures 03.05.02
    - §3.22. The spec allows the connection-oriented or connectionless mode;
    this implementation uses the connection-oriented one - pass an open
    ``P2PConnection``. The Verify Mode of the Management Server shall not be used (see
    the spec's "Use" clause).

    Unlike :func:`~.dmp_mem_write_r_co.dmp_mem_write_r_co`'s
    ``A_Memory_Write`` (not confirmed at the application layer, hence that
    procedure's own ``verify``/``write_delay``), ``A_MemoryExtended_Write``
    (KNX v02.01.01 - Application Layer 03.03.07 - §3.4.9.2) "shall be a
    confirmed service" - its response's ``return_code`` is the completion
    signal for each chunk, so there is nothing here to verify or delay for.
    A device may confirm with either ``E_SUCCESS`` or, at its own discretion,
    ``E_SUCCESS_WITH_CRC`` (§3.4.9.2.1, Table 4) carrying a CRC16-CCITT over
    the count, 24 bit address and data of the chunk. That CRC is checked
    against what was sent; "If the MaS does not use the CRC, the MaC is not
    required to verify the memory" (footnote 12), otherwise use
    :func:`~.dmp_mem_verify_extended_r.dmp_mem_verify_extended_r` for an
    explicit read-back comparison. Only a negative return code (A0h-FFh) is
    an error - the response figures reserve every other value for positive
    confirmations.

    :param conn: Active P2P connection to the device
    :param address: Start address in device memory (0-16777215)
    :param data: Data to write
    :param max_apdu_length: Caps each chunk so its
        A_MemoryExtended_Write-PDU fits within this many octets - the
        device's PID_MAX_APDU_LENGTH (KNX v01.10.01 - Resources 03.05.01 -
        §4.3.7). Defaults to the spec's own fallback of 10 octets of data
        for a device that doesn't support L_Data_Extended frames
        (STANDARD_FRAME_MAX_NPDU_LENGTH minus this service's 5 octet
        header); pass the real value for a device known to support more.
    :raises ValueError: If the address range is out of range, or
        max_apdu_length is not positive
    :raises ManagementConnectionError: If a chunk's response carries a
        negative return code, or echoes a different address than requested
    :raises VerificationError: If a chunk's response carries a CRC that
        doesn't match the data written
    """
    for chunk_address, offset, length in memory_chunks(
        EXTENDED_MEMORY, address, len(data), max_apdu_length, size_name="len(data)"
    ):
        chunk = data[offset : offset + length]
        response = await conn.request(
            apci.MemoryExtendedWrite(address=chunk_address, data=chunk)
        )
        payload = response.payload
        if is_negative_return_code(payload.return_code):
            raise ManagementConnectionError(
                f"Extended memory write failed: address "
                f"{EXTENDED_MEMORY.format_address(chunk_address)} "
                f"return code {payload.return_code:#04x}"
            )
        if payload.address != chunk_address:
            raise ManagementConnectionError(
                f"Extended memory write failed: requested address "
                f"{EXTENDED_MEMORY.format_address(chunk_address)}, response echoed "
                f"{EXTENDED_MEMORY.format_address(payload.address)}"
            )
        if payload.return_code == _E_SUCCESS_WITH_CRC:
            expected_crc = memory_extended_write_crc(chunk_address, chunk)
            if payload.confirmation_data != expected_crc:
                raise VerificationError(
                    f"Extended memory write CRC mismatch at address "
                    f"{EXTENDED_MEMORY.format_address(chunk_address)}: expected "
                    f"{expected_crc.hex()}, got {payload.confirmation_data.hex()}"
                )
