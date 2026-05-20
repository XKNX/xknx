"""DMP_InterfaceObjectRead_R — KNX 03.05.02 §3.27.2 (PDF p. 123)."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.management.protocols import P2PConnection
from xknx.telegram import apci

# nr_of_elem field is 4 bits (KNX 03.03.07 v02.01.01 §3.4.4 Figure 46), max value 2^4 - 1
MAX_ELEMENTS_PER_REQUEST = (1 << 4) - 1


async def dmp_interface_object_read_r(
    connection: P2PConnection,
    object_index: int,
    property_id: int,
    count: int = 1,
    start_index: int = 1,
) -> bytes:
    """
    Read property value(s) from an interface object.

    DMP_InterfaceObjectRead_R — KNX 03.05.02 §3.27.2. Requires an established
    connection (DM_Connect must be executed first).

    :param connection: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param property_id: Property identifier (1-255)
    :param count: Number of elements to read
    :param start_index: Start element index (1-based, 1-4095)
    :return: The property data read from device
    :raises ManagementConnectionError: If device returns error (nr_of_elem = 0)
    """
    # The spec's sequence (A_PropertyDescription_Read) is intentionally skipped:
    # callers supply object_index/property_id/count/start_index explicitly, so the
    # property is always known at this level. Discovery belongs to the Configuration
    # Procedure above (per spec: "shall not interpret ... at the level of this
    # Management Procedure"). Use dmp_interface_object_scan_r to discover properties
    # (type, max_count, access) before calling this function.
    if count <= 0:
        return b""

    data = bytearray()
    remaining = count
    current_index = start_index

    while remaining > 0:
        chunk_count = min(remaining, MAX_ELEMENTS_PER_REQUEST)
        response = await connection.request(
            payload=apci.PropertyValueRead(
                object_index=object_index,
                property_id=property_id,
                count=chunk_count,
                start_index=current_index,
            ),
            expected=apci.PropertyValueResponse,
        )
        # KNX 03.03.07 v02.01.01 §3.4.4.1: "If the remote application process has a problem,
        # e.g., object or Property does not exist or the data does not fit in a PDU
        # or the requester has not the required access rights, then the nr_of_elem
        # of the A_PropertyValue_Response-PDU shall be zero and shall contain no data."
        response_count = response.payload.count
        if response_count == 0:
            raise ManagementConnectionError(
                f"Property read failed: object {object_index} PID {property_id} "
                f"index {current_index} returned nr_of_elem=0"
            )
        # Not in spec: guard against a partial response (non-zero count that doesn't
        # match the request). The spec only mandates nr_of_elem=0 as the error signal,
        # but a mismatch here would silently corrupt the assembled data (wrong byte
        # offsets on subsequent chunks), so we treat it as a hard error.
        if response_count != chunk_count:
            raise ManagementConnectionError(
                f"Property read failed: object {object_index} PID {property_id} "
                f"index {current_index} requested {chunk_count} elements, "
                f"got {response_count}"
            )
        data.extend(response.payload.data)
        current_index += response_count
        remaining -= response_count

    return bytes(data)
