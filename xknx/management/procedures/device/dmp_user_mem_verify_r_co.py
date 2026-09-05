"""DMP_UserMemVerify_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.20.2."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from .const import USER_MEMORY_HEADER_OCTETS, USER_MEMORY_MAX_COUNT

__all__ = ["dmp_user_mem_verify_r_co"]


async def dmp_user_mem_verify_r_co(
    conn: P2PConnection,
    address: int,
    expected_data: bytes,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> None:
    """
    Verify that extended-range device memory matches expected data.

    DMP_UserMemVerify_RCo — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.20.2. Requires an established connection (DM_Connect must be executed
    first). Read-only - unlike DMP_UserMemWrite_RCo's own optional verify,
    this does not write anything first.

    NOTE: the KNX Standard text for this procedure (§3.20.2) is internally
    inconsistent - a copy-paste artifact from DMP_MemVerify_RCo (§3.17.2),
    confirmed against the spec source. Its "Used Application Layer Services"
    clause says plain A_Memory_Read and its maximal-size bullet says 12
    octets (both are DMP_MemVerify_RCo's values), while its own sequence
    diagram correctly shows A_UserMemory_Read-PDU/A_UserMemory_Response-PDU.
    DMP_UserMemRead_RCo (§3.21.2) has the identical prose slip ("subsequent
    A_Memory_Read-PDUs") but the correct 11 octet size, confirming the
    pattern. This implementation follows the sequence diagrams and the actual
    A_UserMemory_* PDU layout (KNX v02.01.01 - Application Layer 03.03.07 -
    §3.5.6.2, 11 octet chunks after the 4 octet header), matching its sibling
    procedures.

    :param conn: Active P2P connection to the device
    :param address: Start address in device memory (0-0xFFFFF)
    :param expected_data: Data the memory is expected to contain
    :param max_apdu_length: Caps each chunk so its A_UserMemory_Response-PDU
        fits within this many octets - the device's PID_MAX_APDU_LENGTH (KNX
        v01.10.01 - Resources 03.05.01 - §4.3.7). Defaults to the spec's
        fallback of 15 octets for a device whose actual value hasn't been
        read; pass the real value for a device known to support more.
    :raises ValueError: If address is out of range, the address range is out
        of range, or max_apdu_length is not positive
    :raises ManagementConnectionError: If a chunk's response carries fewer
        octets than requested, or echoes a different address than requested
    :raises VerificationError: If a block's data doesn't match expected
    """
    if not 0 <= address <= 0xFFFFF:
        raise ValueError(f"address must be 0-0xFFFFF, got {address}")
    if expected_data and address + len(expected_data) - 1 > 0xFFFFF:
        raise ValueError(
            f"address + len(expected_data) - 1 must be <= 0xfffff, got "
            f"{address + len(expected_data) - 1:#07x}"
        )
    if max_apdu_length <= 0:
        raise ValueError(f"max_apdu_length must be positive, got {max_apdu_length}")
    if not expected_data:
        return

    max_chunk_size = min(
        USER_MEMORY_MAX_COUNT, max_apdu_length - USER_MEMORY_HEADER_OCTETS
    )
    if max_chunk_size <= 0:
        raise ValueError(
            f"max_apdu_length {max_apdu_length} leaves no room for memory data "
            f"(header is {USER_MEMORY_HEADER_OCTETS} octets)"
        )

    offset = 0
    current_address = address

    while offset < len(expected_data):
        expected_chunk = expected_data[offset : offset + max_chunk_size]
        response = await conn.request(
            apci.UserMemoryRead(address=current_address, count=len(expected_chunk))
        )
        if response.payload.address != current_address:
            raise ManagementConnectionError(
                f"User memory verify failed: requested address "
                f"{current_address:#07x}, response echoed "
                f"{response.payload.address:#07x}"
            )
        if len(response.payload.data) != len(expected_chunk):
            raise ManagementConnectionError(
                f"User memory verify failed: address {current_address:#07x} "
                f"requested {len(expected_chunk)} octets, "
                f"got {len(response.payload.data)}"
            )
        if response.payload.data != expected_chunk:
            raise VerificationError(
                f"User memory verify mismatch at address {current_address:#07x}: "
                f"expected {expected_chunk.hex()}, got {response.payload.data.hex()}"
            )
        current_address += len(expected_chunk)
        offset += len(expected_chunk)
