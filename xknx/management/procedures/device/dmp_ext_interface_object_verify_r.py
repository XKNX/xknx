"""DMP_ExtInterfaceObjectVerify_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.26.3."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError, PropertyVerificationError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from .const import (
    MAX_EXT_ELEMENTS_PER_REQUEST,
    MAX_EXT_START_INDEX,
    PROPERTY_EXT_VALUE_HEADER_OCTETS,
)

__all__ = ["dmp_ext_interface_object_verify_r"]


async def dmp_ext_interface_object_verify_r(
    conn: P2PConnection,
    object_type: int,
    object_instance: int,
    property_id: int,
    expected_data: bytes,
    count: int = 1,
    start_index: int = 1,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> None:
    """
    Verify a property value of an interface object addressed by type and instance.

    DMP_ExtInterfaceObjectVerify_R — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.26.3. Uses A_PropertyExtValue_Read (KNX v02.01.01 -
    Application Layer 03.03.07 - §3.4.5.1) and compares block by block, as
    the spec's "different or no data received ⇒ error" sits inside the loop.
    Requires an established connection (DM_Connect must be executed first).

    :param conn: Active P2P connection to the device
    :param object_type: Interface Object Type (0-65535)
    :param object_instance: Object Instance (0-4095)
    :param property_id: Property identifier (0-4095)
    :param expected_data: Data the property is expected to contain
    :param count: Number of elements to verify
    :param start_index: Start element index (1-65535)
    :param max_apdu_length: Caps each chunk so its
        A_PropertyExtValue_Response-PDU fits within this many octets - the
        device's PID_MAX_APDU_LENGTH (KNX v01.10.01 - Resources 03.05.01 -
        §4.3.7). Defaults to the spec's fallback of 15 octets.
    :raises ValueError: If count is not positive, expected_data length is
        not divisible by count, start_index is < 1, start_index + count - 1
        exceeds 65535, or max_apdu_length is not positive
    :raises PropertyVerificationError: If a block's data doesn't match expected
    :raises ManagementConnectionError: If a block read fails (nr_of_elem = 0,
        or a response with an element count that doesn't match the request)
    """
    if max_apdu_length <= 0:
        raise ValueError(f"max_apdu_length must be positive, got {max_apdu_length}")
    if count <= 0:
        raise ValueError(f"count must be positive, got {count}")
    # start_index=0 is the element count query (KNX v02.01.01 - Application
    # Layer 03.03.07 - §3.4.5.1), not something this comparison supports.
    if start_index < 1:
        raise ValueError(f"start_index must be >= 1, got {start_index}")
    if start_index + count - 1 > MAX_EXT_START_INDEX:
        raise ValueError(
            f"start_index + count - 1 must be <= {MAX_EXT_START_INDEX}, "
            f"got {start_index + count - 1}"
        )
    if len(expected_data) % count != 0:
        raise ValueError(
            f"expected_data length {len(expected_data)} must be divisible by "
            f"element count {count}"
        )

    # As in dmp_interface_object_verify_r, the PID is always supplied by the
    # caller, so the spec's optional A_PropertyExtDescription_Read step never
    # applies here.
    element_size = len(expected_data) // count
    max_elements_per_chunk = min(
        MAX_EXT_ELEMENTS_PER_REQUEST,
        max(1, (max_apdu_length - PROPERTY_EXT_VALUE_HEADER_OCTETS) // element_size),
    )

    remaining = count
    current_index = start_index
    data_offset = 0

    while remaining > 0:
        chunk_count = min(remaining, max_elements_per_chunk)
        expected_chunk = expected_data[
            data_offset : data_offset + chunk_count * element_size
        ]

        response = await conn.request(
            payload=apci.PropertyExtValueRead(
                interface_object_type=object_type,
                object_instance=object_instance,
                property_id=property_id,
                nr_of_elem=chunk_count,
                start_index=current_index,
            ),
        )

        response_count = response.payload.nr_of_elem
        if response_count == 0:
            raise ManagementConnectionError(
                f"Property verify failed: object type {object_type} instance "
                f"{object_instance} PID {property_id} index {current_index} "
                f"returned nr_of_elem=0 (error {response.payload.data.hex()})"
            )
        if response_count != chunk_count:
            raise ManagementConnectionError(
                f"Property verify failed: object type {object_type} instance "
                f"{object_instance} PID {property_id} index {current_index} "
                f"requested {chunk_count} elements, got {response_count}"
            )
        if response.payload.data != expected_chunk:
            raise PropertyVerificationError(
                f"Property verify mismatch: object type {object_type} instance "
                f"{object_instance} PID {property_id} index {current_index}: "
                f"expected {expected_chunk.hex()}, "
                f"got {response.payload.data.hex()}"
            )

        current_index += response_count
        remaining -= response_count
        data_offset += response_count * element_size
