"""DMP_InterfaceObjectWrite_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.25.2."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError, PropertyVerificationError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from .const import MAX_ELEMENTS_PER_REQUEST

__all__ = ["dmp_interface_object_write_r"]


async def dmp_interface_object_write_r(
    conn: P2PConnection,
    object_index: int,
    property_id: int,
    data: bytes,
    count: int = 1,
    start_index: int = 1,
    verify: bool = False,
) -> bytes:
    """
    Write property value(s) to an interface object.

    DMP_InterfaceObjectWrite_R — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.25.2. Requires an established connection (DM_Connect must be executed
    first).

    :param conn: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param property_id: Property identifier (1-255)
    :param data: Data to write
    :param count: Number of elements to write
    :param start_index: Start element index (1-based, 1-4095)
    :param verify: If True, verify response data matches written data
    :return: The response data from device (concatenated for chunked writes)
    :raises ValueError: If count is not positive, or data length is not
        divisible by count
    :raises PropertyVerificationError: If verify is enabled and the response differs
    :raises ManagementConnectionError: If device returns error (nr_of_elem =
        0), or a response with an element count that doesn't match the request
    """
    # DMP_InterfaceObjectWrite_R's own parameter list (KNX v02.01.02 -
    # Management Procedures 03.05.02 - §3.25.1: object_type, object_index,
    # PID, start_index, noElements) only ever supplies a PID, so the spec's
    # optional A_PropertyDescription_Read step - "if Property... is unknown
    # to the Management Client" - never applies here: the property is always
    # known by definition. Use dmp_interface_object_scan_r (KNX v02.01.02 -
    # Management Procedures 03.05.02 - §3.28.2) to discover a device's
    # properties (type, max_count, access) first if you don't already know
    # which PID to write.
    if count <= 0:
        raise ValueError(f"count must be positive, got {count}")
    if not data:
        return b""

    if len(data) % count != 0:
        raise ValueError(
            f"Data length {len(data)} must be divisible by element count {count}"
        )

    element_size = len(data) // count
    result = bytearray()
    remaining = count
    current_index = start_index
    data_offset = 0

    while remaining > 0:
        chunk_count = min(remaining, MAX_ELEMENTS_PER_REQUEST)
        chunk_data = data[data_offset : data_offset + chunk_count * element_size]

        response = await conn.request(
            payload=apci.PropertyValueWrite(
                object_index=object_index,
                property_id=property_id,
                count=chunk_count,
                start_index=current_index,
                data=chunk_data,
            ),
            expected=apci.PropertyValueResponse,
        )
        # `expected` guarantees this via `P2PConnection._receive`
        assert isinstance(response.payload, apci.PropertyValueResponse)

        # KNX v02.01.01 - Application Layer 03.03.07 - §3.4.4.2: "If the remote
        # application process has a problem, e.g., Interface Object or Property
        # doesn't exist or the requester does not have the required access
        # rights, then the nr_of_elem of the A_PropertyValue_Response-PDU
        # shall be zero and shall contain no data."
        response_count = response.payload.count
        if response_count == 0:
            raise ManagementConnectionError(
                f"Property write failed: object {object_index} PID {property_id} "
                f"index {current_index} returned nr_of_elem=0"
            )
        # Not in spec: guard against a partial response (non-zero count that doesn't
        # match the request). The spec only mandates nr_of_elem=0 as the error signal,
        # but a mismatch here would silently corrupt the assembled result (wrong byte
        # offsets on subsequent chunks), so we treat it as a hard error.
        if response_count != chunk_count:
            raise ManagementConnectionError(
                f"Property write failed: object {object_index} PID {property_id} "
                f"index {current_index} requested {chunk_count} elements, "
                f"got {response_count}"
            )

        if verify and response.payload.data != chunk_data:
            raise PropertyVerificationError(
                f"Property verify mismatch at object {object_index} PID {property_id} "
                f"index {current_index}: expected {chunk_data.hex()}, "
                f"got {response.payload.data.hex()}"
            )

        result.extend(response.payload.data)
        current_index += response_count
        remaining -= response_count
        data_offset += response_count * element_size

    return bytes(result)
