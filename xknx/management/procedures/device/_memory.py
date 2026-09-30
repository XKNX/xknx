"""
Shared address validation and chunking of the memory procedures.

The A_Memory_*, A_UserMemory_* and A_MemoryExtended_* procedures all split a
transfer into chunks bounded by the service's count field and by
``max_apdu_length``, and reject an address range that doesn't fit their
address space before sending anything. Only the address space and the PDU
header differ, which :class:`MemorySpace` describes.
"""

from __future__ import annotations

import binascii
from dataclasses import dataclass

from .const import (
    MEMORY_EXTENDED_HEADER_OCTETS,
    MEMORY_EXTENDED_MAX_COUNT,
    MEMORY_HEADER_OCTETS,
    MEMORY_MAX_COUNT,
    USER_MEMORY_HEADER_OCTETS,
    USER_MEMORY_MAX_COUNT,
)


@dataclass(frozen=True, slots=True)
class MemorySpace:
    """An address space and the PDU layout used to access it."""

    max_address: int
    address_text: str
    header_octets: int
    max_count: int

    def format_address(self, address: int) -> str:
        """Format an address zero-padded to this space's width."""
        return f"{address:#0{len(f'{self.max_address:#x}')}x}"


MEMORY = MemorySpace(0xFFFF, "65535", MEMORY_HEADER_OCTETS, MEMORY_MAX_COUNT)
USER_MEMORY = MemorySpace(
    0xFFFFF, "0xFFFFF", USER_MEMORY_HEADER_OCTETS, USER_MEMORY_MAX_COUNT
)
EXTENDED_MEMORY = MemorySpace(
    0xFFFFFF, "16777215", MEMORY_EXTENDED_HEADER_OCTETS, MEMORY_EXTENDED_MAX_COUNT
)


def memory_chunks(
    space: MemorySpace,
    address: int,
    size: int,
    max_apdu_length: int,
    *,
    size_name: str = "size",
) -> list[tuple[int, int, int]]:
    """
    Validate a transfer and split it into chunks.

    :param size_name: How the size is named in error messages, e.g.
        ``"len(data)"``
    :return: ``(address, offset, length)`` of every chunk, in order
    :raises ValueError: If ``size`` is negative, the address range doesn't
        fit ``space``, or ``max_apdu_length`` leaves no room for data
    """
    if size < 0:
        raise ValueError(f"size must be >= 0, got {size}")
    if not 0 <= address <= space.max_address:
        raise ValueError(f"address must be 0-{space.address_text}, got {address}")
    if size and address + size - 1 > space.max_address:
        raise ValueError(
            f"address + {size_name} - 1 must be <= {space.max_address:#x}, got "
            f"{space.format_address(address + size - 1)}"
        )
    if max_apdu_length <= 0:
        raise ValueError(f"max_apdu_length must be positive, got {max_apdu_length}")
    if not size:
        return []

    max_chunk_size = min(space.max_count, max_apdu_length - space.header_octets)
    if max_chunk_size <= 0:
        raise ValueError(
            f"max_apdu_length {max_apdu_length} leaves no room for memory data "
            f"(header is {space.header_octets} octets)"
        )
    return [
        (address + offset, offset, min(max_chunk_size, size - offset))
        for offset in range(0, size, max_chunk_size)
    ]


# KNX v02.01.01 - Application Layer 03.03.07 - §3.4.8.3/§3.4.9: negative
# return codes are A0h-FFh. The A_MemoryExtended_*_Response figures reserve
# every other value for (future) positive confirmations, so only A0h-FFh is
# an error.
_MIN_NEGATIVE_RETURN_CODE = 0xA0

# CRC16-CCITT as KNX defines it (KNX v02.01.01 - Application Layer 03.03.07 -
# §3.4.9.2.1 footnote 13, "Initial value = FFFFh ... Same CRC as in System
# B"). KNX v01.10.01 - Resources 03.05.01 - §4.2.27.1.2 gives the same
# parameters with the check value "The correct CRC16-CCITT of the string
# '123456789' is E5CCh" - the augmented form, whose FFFFh initial value is
# 1D0Fh in the direct form binascii.crc_hqx() computes (calimero-core's
# ManagementClientImpl.crc16Ccitt() agrees).
_CRC16_CCITT_KNX_INIT = 0x1D0F


def is_negative_return_code(return_code: int) -> bool:
    """Return whether a memory service return code is negative (A0h-FFh)."""
    return return_code >= _MIN_NEGATIVE_RETURN_CODE


def memory_extended_write_crc(address: int, data: bytes) -> bytes:
    """
    Return the CRC an E_SUCCESS_WITH_CRC A_MemoryExtended_Write_Response carries.

    §3.4.9.2.1 Table 4: "CRC16-CCITT beginning after the APCI Octet, over
    received data including address and number of data octets" - i.e. over
    count (1) + 24 bit address (3) + data, as the 2 octet big-endian value.
    """
    crc = binascii.crc_hqx(
        bytes([len(data)]) + address.to_bytes(3, "big") + data, _CRC16_CCITT_KNX_INIT
    )
    return crc.to_bytes(2, "big")
