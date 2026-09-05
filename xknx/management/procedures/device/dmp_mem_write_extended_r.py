"""DMP_MemWrite_Extended_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.22."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from .const import MEMORY_EXTENDED_HEADER_OCTETS, MEMORY_EXTENDED_MAX_COUNT

__all__ = ["dmp_mem_write_extended_r"]

# KNX v02.01.01 - Application Layer 03.03.07 - §3.4.9.2.1, Table 4 "Write
# Return Codes": 01h is a second positive code specific to
# A_MemoryExtended_Write_Response ("CRC over original data"), not part of
# the generic device management schema apci.ReturnCode covers - a device
# may confirm a write with a CRC16-CCITT instead of a bare E_SUCCESS,
# entirely at its own discretion (footnote 12: "[w]hether or not the MaS
# replies with a CRC is implementation dependent"). Treated as success here;
# the CRC itself is not verified - use dmp_mem_verify_extended_r for an
# explicit read-back comparison instead.
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
    - §3.22. Requires an established connection (DM_Connect must be executed
    first). The Verify Mode of the Management Server shall not be used (see
    the spec's "Use" clause).

    Unlike :func:`~.dmp_mem_write_r_co.dmp_mem_write_r_co`'s
    ``A_Memory_Write`` (not confirmed at the application layer, hence that
    procedure's own ``verify``/``write_delay``), ``A_MemoryExtended_Write``
    (KNX v02.01.01 - Application Layer 03.03.07 - §3.4.9.2) "shall be a
    confirmed service" - its response's ``return_code`` is the completion
    signal for each chunk, so there is nothing here to verify or delay for.
    A device may confirm with either ``E_SUCCESS`` or, at its own discretion,
    a positive ``E_SUCCESS_WITH_CRC`` (§3.4.9.2.1, Table 4) carrying a
    CRC16-CCITT over the chunk just written - both are accepted as success
    here; the CRC itself is not verified, use
    :func:`~.dmp_mem_verify_extended_r.dmp_mem_verify_extended_r` for an
    explicit read-back comparison instead.

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
    """
    if not 0 <= address <= 0xFFFFFF:
        raise ValueError(f"address must be 0-16777215, got {address}")
    if data and address + len(data) - 1 > 0xFFFFFF:
        raise ValueError(
            f"address + len(data) - 1 must be <= 0xffffff, got "
            f"{address + len(data) - 1:#08x}"
        )
    if max_apdu_length <= 0:
        raise ValueError(f"max_apdu_length must be positive, got {max_apdu_length}")
    if not data:
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

    while offset < len(data):
        chunk = data[offset : offset + max_chunk_size]
        response = await conn.request(
            apci.MemoryExtendedWrite(address=current_address, data=chunk)
        )
        payload = response.payload
        if payload.return_code not in (
            apci.ReturnCode.E_SUCCESS.value,
            _E_SUCCESS_WITH_CRC,
        ):
            raise ManagementConnectionError(
                f"Extended memory write failed: address {current_address:#08x} "
                f"return code {payload.return_code:#04x}"
            )
        if payload.address != current_address:
            raise ManagementConnectionError(
                f"Extended memory write failed: requested address "
                f"{current_address:#08x}, response echoed {payload.address:#08x}"
            )
        current_address += len(chunk)
        offset += len(chunk)
