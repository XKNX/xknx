"""DMP_InterfaceObjectRead_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.27.2."""

from __future__ import annotations

from xknx.cemi.const import STANDARD_FRAME_MAX_NPDU_LENGTH
from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

from .const import MAX_ELEMENTS_PER_REQUEST, PROPERTY_VALUE_HEADER_OCTETS

__all__ = ["dmp_interface_object_read_r"]


async def dmp_interface_object_read_r(
    conn: P2PConnection,
    object_index: int,
    property_id: int,
    count: int = 1,
    start_index: int = 1,
    max_apdu_length: int = STANDARD_FRAME_MAX_NPDU_LENGTH,
    element_size: int = 1,
) -> bytes:
    """
    Read property value(s) from an interface object.

    DMP_InterfaceObjectRead_R — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.27.2. Requires an established connection (DM_Connect must be executed
    first).

    :param conn: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param property_id: Property identifier (1-255)
    :param count: Number of elements to read
    :param start_index: Start element index (1-based, 1-4095)
    :param max_apdu_length: Caps each chunk so its A_PropertyValue_Response-PDU
        fits within this many octets - the device's PID_MAX_APDU_LENGTH (KNX
        v01.10.01 - Resources 03.05.01 - §4.3.7). Defaults to the spec's
        fallback of 15 octets for a device whose actual value hasn't been
        read; pass the real value for a device known to support more.
    :param element_size: Octet size of a single Property element (from its
        PDT, e.g. via a preceding A_PropertyDescription_Read). Used together
        with max_apdu_length to size chunks; the default of 1 is only correct
        for byte-sized properties - an incorrect value can undersize *or*
        oversize chunks, so pass the real size for anything wider.
        TODO: derive this automatically instead of requiring the caller to
        pass it - issue an A_PropertyDescription_Read for the PDT (KNX
        v02.01.01 - Application Layer 03.03.07 - §3.4.3) and look it up in a
        PDT -> byte-size table, as Calimero's
        ManagementClientImpl.readProperty/PropertyTypes.bitSize does. Needs a
        PDT size table, which xknx doesn't have yet.
    :return: The property data read from device
    :raises ValueError: If count is not positive, start_index is < 1, or
        max_apdu_length is not positive
    :raises ManagementConnectionError: If device returns error (nr_of_elem = 0)
        or a response with an element count that doesn't match the request
    """
    if max_apdu_length <= 0:
        raise ValueError(f"max_apdu_length must be positive, got {max_apdu_length}")
    # DMP_InterfaceObjectRead_R's own parameter list (KNX v02.01.02 -
    # Management Procedures 03.05.02 - §3.27.1: object_type, object_index,
    # PID, start_index, noElements) only ever supplies a PID, so the spec's
    # optional A_PropertyDescription_Read step - "if Property... is unknown
    # to the Management Client" - never applies here: the property is always
    # known by definition. Use dmp_interface_object_scan_r (KNX v02.01.02 -
    # Management Procedures 03.05.02 - §3.28.2) to discover a device's
    # properties (type, max_count, access) first if you don't already know
    # which PID to read.
    if count <= 0:
        raise ValueError(f"count must be positive, got {count}")
    # KNX v02.01.01 - Application Layer 03.03.07 - §3.4.4.1: start_index=0
    # with nr_of_elem>1 is a distinct "read the current element count"
    # request that answers with nr_of_elem=1 and the count in `data`, not
    # the requested elements - not something this chunked byte-read supports.
    if start_index < 1:
        raise ValueError(f"start_index must be >= 1, got {start_index}")

    max_elements_per_chunk = min(
        MAX_ELEMENTS_PER_REQUEST,
        max(1, (max_apdu_length - PROPERTY_VALUE_HEADER_OCTETS) // element_size),
    )

    data = bytearray()
    remaining = count
    current_index = start_index

    while remaining > 0:
        chunk_count = min(remaining, max_elements_per_chunk)
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
        # KNX v02.01.01 - Application Layer 03.03.07 - §3.4.4.1: "If the remote
        # application process has a problem, e.g., object or Property does not
        # exist or the data does not fit in a PDU or the requester has not the
        # required access rights, then the nr_of_elem of the
        # A_PropertyValue_Response-PDU shall be zero and shall contain no data."
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
