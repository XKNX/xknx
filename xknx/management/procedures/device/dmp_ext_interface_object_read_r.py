"""DMP_ExtInterfaceObjectRead_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.27.4."""

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

__all__ = ["dmp_ext_interface_object_read_r"]


async def dmp_ext_interface_object_read_r(
    conn: P2PConnection,
    object_type: int,
    object_instance: int,
    property_id: int,
    count: int = 1,
    start_index: int = 1,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
) -> bytes:
    """
    Read property value(s) from an interface object addressed by type and instance.

    DMP_ExtInterfaceObjectRead_R — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.27.4. Uses A_PropertyExtValue_Read (KNX v02.01.01 -
    Application Layer 03.03.07 - §3.4.5.1), so the interface object is
    addressed by its Interface Object Type and Object Instance instead of
    its object index. Requires an established connection (DM_Connect must be
    executed first).

    Like dmp_interface_object_read_r, the first request reads exactly 1
    element to learn the element size, since the PDU carries no Property
    Datatype; every request after that is sized against max_apdu_length.

    :param conn: Active P2P connection to the device
    :param object_type: Interface Object Type (0-65535)
    :param object_instance: Object Instance (0-4095)
    :param property_id: Property identifier (0-4095)
    :param count: Number of elements to read
    :param start_index: Start element index (0-65535). 0 reads the
        Property's current element count (KNX v02.01.01 - Application Layer
        03.03.07 - §3.4.5.1) and is only valid together with count=1; the
        returned bytes are that count - decode with
        int.from_bytes(data, "big").
    :param max_apdu_length: Caps each chunk (after the first) so its
        A_PropertyExtValue_Response-PDU fits within this many octets - the
        device's PID_MAX_APDU_LENGTH (KNX v01.10.01 - Resources 03.05.01 -
        §4.3.7). Defaults to the spec's fallback of 15 octets.
    :return: The property data read from device
    :raises ValueError: If count is not positive, start_index is negative,
        start_index is 0 with count != 1, start_index + count - 1 exceeds
        65535, or max_apdu_length is not positive
    :raises ManagementConnectionError: If device returns error (nr_of_elem =
        0), a response with an element count that doesn't match the request,
        or the probe response has empty data
    """
    if max_apdu_length <= 0:
        raise ValueError(f"max_apdu_length must be positive, got {max_apdu_length}")
    # As in dmp_interface_object_read_r, the PID is always supplied by the
    # caller, so the spec's optional A_PropertyExtDescription_Read step - "if
    # Property of management control is unknown to the Management Client" -
    # never applies here.
    if count <= 0:
        raise ValueError(f"count must be positive, got {count}")
    if start_index < 0:
        raise ValueError(f"start_index must be >= 0, got {start_index}")
    # KNX v02.01.01 - Application Layer 03.03.07 - §3.4.5.1: start_index=0
    # is answered with nr_of_elem=1 and the current element count in `data`.
    if start_index == 0 and count != 1:
        raise ValueError(
            f"start_index=0 (element count query) requires count=1, got {count}"
        )
    if start_index + count - 1 > MAX_EXT_START_INDEX:
        raise ValueError(
            f"start_index + count - 1 must be <= {MAX_EXT_START_INDEX}, "
            f"got {start_index + count - 1}"
        )

    data = bytearray()
    remaining = count
    current_index = start_index
    max_elements_per_chunk = 1
    element_size: int | None = None

    while remaining > 0:
        chunk_count = min(remaining, max_elements_per_chunk)
        response = await conn.request(
            payload=apci.PropertyExtValueRead(
                interface_object_type=object_type,
                object_instance=object_instance,
                property_id=property_id,
                nr_of_elem=chunk_count,
                start_index=current_index,
            ),
        )
        # KNX v02.01.01 - Application Layer 03.03.07 - §3.4.5.1: "If the MaS
        # has a problem, e.g., Interface Object or Property does not exist,
        # then the nr_of_elem shall be set to zero [...]. The data field of a
        # negative response shall contain error information."
        response_count = response.payload.nr_of_elem
        if response_count == 0:
            raise ManagementConnectionError(
                f"Property read failed: object type {object_type} instance "
                f"{object_instance} PID {property_id} index {current_index} "
                f"returned nr_of_elem=0 (error {response.payload.data.hex()})"
            )
        # Not in spec: a partial response would corrupt the assembled data.
        if response_count != chunk_count:
            raise ManagementConnectionError(
                f"Property read failed: object type {object_type} instance "
                f"{object_instance} PID {property_id} index {current_index} "
                f"requested {chunk_count} elements, got {response_count}"
            )

        if element_size is None:
            element_size = len(response.payload.data)
            if element_size == 0:
                raise ManagementConnectionError(
                    f"Property read failed: object type {object_type} instance "
                    f"{object_instance} PID {property_id} index {current_index} "
                    "returned empty data for 1 element"
                )
            max_elements_per_chunk = min(
                MAX_EXT_ELEMENTS_PER_REQUEST,
                max(
                    1,
                    (max_apdu_length - PROPERTY_EXT_VALUE_HEADER_OCTETS)
                    // element_size,
                ),
            )

        data.extend(response.payload.data)
        current_index += response_count
        remaining -= response_count

    return bytes(data)
