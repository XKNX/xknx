"""DMP_UserMemVerify_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.20.2."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError, VerificationError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from ._memory import USER_MEMORY, memory_chunks

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
    for chunk_address, offset, length in memory_chunks(
        USER_MEMORY,
        address,
        len(expected_data),
        max_apdu_length,
        size_name="len(expected_data)",
    ):
        expected_chunk = expected_data[offset : offset + length]
        response = await conn.request(
            apci.UserMemoryRead(address=chunk_address, count=length)
        )
        payload = response.payload
        if payload.address != chunk_address:
            raise ManagementConnectionError(
                f"User memory verify failed: requested address "
                f"{USER_MEMORY.format_address(chunk_address)}, response echoed "
                f"{USER_MEMORY.format_address(payload.address)}"
            )
        if len(payload.data) != length:
            raise ManagementConnectionError(
                f"User memory verify failed: address "
                f"{USER_MEMORY.format_address(chunk_address)} requested "
                f"{length} octets, got {len(payload.data)}"
            )
        if payload.data != expected_chunk:
            raise VerificationError(
                f"User memory verify mismatch at address "
                f"{USER_MEMORY.format_address(chunk_address)}: "
                f"expected {expected_chunk.hex()}, got {payload.data.hex()}"
            )
