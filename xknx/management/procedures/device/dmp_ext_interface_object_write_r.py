"""
DMP_ExtInterfaceObjectWriteCon_R and DMP_ExtInterfaceObjectWriteUnCon_R.

KNX v02.01.02 - Management Procedures 03.05.02 - §3.25.4 and §3.25.5.
"""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from .const import (
    MAX_EXT_ELEMENTS_PER_REQUEST,
    MAX_EXT_START_INDEX,
    PROPERTY_EXT_VALUE_HEADER_OCTETS,
)

__all__ = [
    "dmp_ext_interface_object_write_con_r",
    "dmp_ext_interface_object_write_uncon_r",
]


def _chunks(
    data: bytes,
    count: int,
    start_index: int,
    max_apdu_length: int,
) -> list[tuple[int, int, bytes]]:
    """Split a write into (start_index, nr_of_elem, data) blocks."""
    if max_apdu_length <= 0:
        raise ValueError(f"max_apdu_length must be positive, got {max_apdu_length}")
    if count <= 0:
        raise ValueError(f"count must be positive, got {count}")
    if start_index < 0:
        raise ValueError(f"start_index must be >= 0, got {start_index}")
    if len(data) % count != 0:
        raise ValueError(
            f"Data length {len(data)} must be divisible by element count {count}"
        )
    # Checked up front so a later block can't fail after earlier ones were
    # already written.
    if start_index + count - 1 > MAX_EXT_START_INDEX:
        raise ValueError(
            f"start_index + count - 1 must be <= {MAX_EXT_START_INDEX}, "
            f"got {start_index + count - 1}"
        )
    if not data:
        return []

    element_size = len(data) // count
    per_chunk = min(
        MAX_EXT_ELEMENTS_PER_REQUEST,
        max(1, (max_apdu_length - PROPERTY_EXT_VALUE_HEADER_OCTETS) // element_size),
    )
    blocks = []
    for offset in range(0, count, per_chunk):
        chunk_count = min(per_chunk, count - offset)
        blocks.append(
            (
                start_index + offset,
                chunk_count,
                data[offset * element_size : (offset + chunk_count) * element_size],
            )
        )
    return blocks


async def dmp_ext_interface_object_write_con_r(
    conn: P2PConnection,
    object_type: int,
    object_instance: int,
    property_id: int,
    data: bytes,
    count: int = 1,
    start_index: int = 1,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> None:
    """
    Write property value(s) to an interface object addressed by type and instance.

    DMP_ExtInterfaceObjectWriteCon_R — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.25.4. Uses A_PropertyExtValue_WriteCon (KNX v02.01.01 -
    Application Layer 03.03.07 - §3.4.5.2); every block is confirmed by an
    A_PropertyExtValue_WriteConRes-PDU and "RR ≠ 0 ⇒ error". Requires an
    established connection (DM_Connect must be executed first).

    :param conn: Active P2P connection to the device
    :param object_type: Interface Object Type (0-65535)
    :param object_instance: Object Instance (0-4095)
    :param property_id: Property identifier (0-4095)
    :param data: Data to write
    :param count: Number of elements to write
    :param start_index: Start element index (0-65535)
    :param max_apdu_length: Caps each block so its
        A_PropertyExtValue_WriteCon-PDU fits within this many octets - the
        device's PID_MAX_APDU_LENGTH (KNX v01.10.01 - Resources 03.05.01 -
        §4.3.7). Defaults to the spec's fallback of 15 octets.
    :raises ValueError: If count is not positive, start_index is negative,
        data length is not divisible by count, start_index + count - 1
        exceeds 65535, or max_apdu_length is not positive
    :raises ManagementConnectionError: If the device answers a block with a
        return code other than E_SUCCESS, or with an element count or start
        index that doesn't match the request
    """
    # As in dmp_interface_object_write_r, the PID is always supplied by the
    # caller, so the spec's optional A_PropertyExtDescription_Read step - "if
    # Property of management control is unknown to the Management Client" -
    # never applies here.
    for index, chunk_count, chunk in _chunks(data, count, start_index, max_apdu_length):
        response = await conn.request(
            payload=apci.PropertyExtValueWriteCon(
                interface_object_type=object_type,
                object_instance=object_instance,
                property_id=property_id,
                nr_of_elem=chunk_count,
                start_index=index,
                data=chunk,
            ),
        )
        result = response.payload
        if result.return_code != apci.ReturnCode.E_SUCCESS:
            raise ManagementConnectionError(
                f"Property write failed: object type {object_type} instance "
                f"{object_instance} PID {property_id} index {index} "
                f"returned {result.return_code.name}"
            )
        # Not in spec: the response must confirm the block that was sent.
        if result.nr_of_elem != chunk_count or result.start_index != index:
            raise ManagementConnectionError(
                f"Property write failed: object type {object_type} instance "
                f"{object_instance} PID {property_id} wrote {chunk_count} elements "
                f"at index {index}, confirmed {result.nr_of_elem} at index "
                f"{result.start_index}"
            )


async def dmp_ext_interface_object_write_uncon_r(
    conn: P2PConnection,
    object_type: int,
    object_instance: int,
    property_id: int,
    data: bytes,
    count: int = 1,
    start_index: int = 1,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> None:
    """
    Write property value(s) to an interface object without confirmation.

    DMP_ExtInterfaceObjectWriteUnCon_R — KNX v02.01.02 - Management
    Procedures 03.05.02 - §3.25.5. Uses A_PropertyExtValue_WriteUnCon (KNX
    v02.01.01 - Application Layer 03.03.07 - §3.4.5.3), which has no
    response, so a block the device rejects goes unnoticed - use
    dmp_ext_interface_object_verify_r or
    dmp_ext_interface_object_write_con_r where that matters. Requires an
    established connection (DM_Connect must be executed first).

    :param conn: Active P2P connection to the device
    :param object_type: Interface Object Type (0-65535)
    :param object_instance: Object Instance (0-4095)
    :param property_id: Property identifier (0-4095)
    :param data: Data to write
    :param count: Number of elements to write
    :param start_index: Start element index (0-65535)
    :param max_apdu_length: Caps each block so its
        A_PropertyExtValue_WriteUnCon-PDU fits within this many octets - the
        device's PID_MAX_APDU_LENGTH (KNX v01.10.01 - Resources 03.05.01 -
        §4.3.7). Defaults to the spec's fallback of 15 octets.
    :raises ValueError: If count is not positive, start_index is negative,
        data length is not divisible by count, start_index + count - 1
        exceeds 65535, or max_apdu_length is not positive
    """
    for index, chunk_count, chunk in _chunks(data, count, start_index, max_apdu_length):
        await conn.send_data(
            apci.PropertyExtValueWriteUnCon(
                interface_object_type=object_type,
                object_instance=object_instance,
                property_id=property_id,
                nr_of_elem=chunk_count,
                start_index=index,
                data=chunk,
            )
        )
