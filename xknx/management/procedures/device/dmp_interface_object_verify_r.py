"""DMP_InterfaceObjectVerify_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.26.2."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError, PropertyVerificationError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from .const import MAX_ELEMENTS_PER_REQUEST

__all__ = ["dmp_interface_object_verify_r"]


async def dmp_interface_object_verify_r(
    conn: P2PConnection,
    object_index: int,
    property_id: int,
    expected_data: bytes,
    count: int = 1,
    start_index: int = 1,
) -> None:
    """
    Verify that a device's property value matches expected data, block by block.

    DMP_InterfaceObjectVerify_R — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.26.2. Requires an established connection (DM_Connect must be executed
    first). Per-block comparison satisfies the spec's "different or no data
    received ⇒ error" note inside the loop.

    :param conn: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param property_id: Property identifier (1-255)
    :param expected_data: Data the property is expected to contain
    :param count: Number of elements to verify
    :param start_index: Start element index (1-based, 1-4095)
    :raises ValueError: If count is not positive, or expected_data length is
        not divisible by count
    :raises PropertyVerificationError: If a block's data doesn't match expected
    :raises ManagementConnectionError: If a block read fails (nr_of_elem = 0,
        or a response with an element count that doesn't match the request)
    """
    if count <= 0:
        raise ValueError(f"count must be positive, got {count}")

    if len(expected_data) % count != 0:
        raise ValueError(
            f"expected_data length {len(expected_data)} must be divisible by element count {count}"
        )

    # DMP_InterfaceObjectVerify_R's own parameter list (KNX v02.01.02 -
    # Management Procedures 03.05.02 - §3.26.1: object_type, object_index,
    # PID, start_index, noElements) only ever supplies a PID, so the spec's
    # optional A_PropertyDescription_Read step - "if Property... is unknown
    # to the Management Client" - never applies here: the property is always
    # known by definition. Use dmp_interface_object_scan_r (KNX v02.01.02 -
    # Management Procedures 03.05.02 - §3.28.2) to discover a device's
    # properties (type, max_count, access) first if you don't already know
    # which PID to verify.
    #
    # The loop below inlines the read to compare per block, as the spec requires
    # ("different or no data received ⇒ error" is inside the loop). A simpler but
    # less spec-compliant alternative would be to call dmp_interface_object_read_r
    # and compare the assembled result against expected_data in one shot.
    element_size = len(expected_data) // count
    remaining = count
    current_index = start_index
    data_offset = 0

    while remaining > 0:
        chunk_count = min(remaining, MAX_ELEMENTS_PER_REQUEST)
        expected_chunk = expected_data[
            data_offset : data_offset + chunk_count * element_size
        ]

        response = await conn.request(
            payload=apci.PropertyValueRead(
                object_index=object_index,
                property_id=property_id,
                count=chunk_count,
                start_index=current_index,
            ),
            expected=apci.PropertyValueResponse,
        )
        # `expected` guarantees this via `P2PConnection._receive`
        assert isinstance(response.payload, apci.PropertyValueResponse)

        response_count = response.payload.count
        if response_count == 0:
            raise ManagementConnectionError(
                f"Property verify failed: object {object_index} PID {property_id} "
                f"index {current_index} returned nr_of_elem=0"
            )
        if response_count != chunk_count:
            raise ManagementConnectionError(
                f"Property verify failed: object {object_index} PID {property_id} "
                f"index {current_index} requested {chunk_count} elements, "
                f"got {response_count}"
            )
        if response.payload.data != expected_chunk:
            raise PropertyVerificationError(
                f"Property verify mismatch: object {object_index} PID {property_id} "
                f"index {current_index}: expected {expected_chunk.hex()}, "
                f"got {response.payload.data.hex()}"
            )

        current_index += response_count
        remaining -= response_count
        data_offset += response_count * element_size
