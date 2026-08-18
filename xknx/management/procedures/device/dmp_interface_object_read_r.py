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
) -> bytes:
    """
    Read property value(s) from an interface object.

    DMP_InterfaceObjectRead_R — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.27.2. Requires an established connection (DM_Connect must be executed
    first).

    The wire PDU carries no Property element size (PDT), so for count > 1 the
    first request always reads exactly 1 element to safely learn it - a
    single element is the smallest possible request, so it's the only size
    that's safe to ask for without already knowing the answer. Every request
    after that is sized against max_apdu_length using the now-known element
    size, so a wide-element property is chunked correctly from the start
    instead of failing outright on an oversized first guess.

    :param conn: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param property_id: Property identifier (1-255)
    :param count: Number of elements to read
    :param start_index: Start element index (0-4095). 0 is a special case
        (KNX v02.01.01 - Application Layer 03.03.07 - §3.4.4.1): the device
        answers with the Property's current element count instead of real
        array data, in a single fixed-shape exchange - only valid together
        with count=1. In that case, the returned bytes are the count itself,
        encoded as unsigned16 or unsigned32 depending on the Property's
        max_nr_of_elem exponent (KNX v02.01.01 - Application Interface Layer
        03.04.01 - §4.3.2.3) - decode with int.from_bytes(data, "big").
    :param max_apdu_length: Caps each chunk (after the first) so its
        A_PropertyValue_Response-PDU fits within this many octets - the
        device's PID_MAX_APDU_LENGTH (KNX v01.10.01 - Resources 03.05.01 -
        §4.3.7). Defaults to the spec's fallback of 15 octets for a device
        whose actual value hasn't been read; pass the real value for a device
        known to support more.
    :return: The property data read from device
    :raises ValueError: If count is not positive, start_index is negative,
        start_index is 0 with count != 1, start_index + count - 1 exceeds
        4095, or max_apdu_length is not positive
    :raises ManagementConnectionError: If device returns error (nr_of_elem =
        0), a response with an element count that doesn't match the request,
        or the probe response has empty data
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
    if start_index < 0:
        raise ValueError(f"start_index must be >= 0, got {start_index}")
    # KNX v02.01.01 - Application Layer 03.03.07 - §3.4.4.1: start_index=0 is
    # a distinct "read the current element count" request answered with
    # nr_of_elem=1 and the count in `data`, not real array data. Restricting
    # to count=1 keeps this safe to run through the same chunking loop below
    # unmodified: it becomes the only (and last) iteration, so there's no
    # second request that would otherwise misinterpret the count bytes as
    # real array data and continue reading from the wrong index.
    if start_index == 0 and count != 1:
        raise ValueError(
            f"start_index=0 (element count query) requires count=1, got {count}"
        )
    # start_index (12 bits) and count (4 bits) are independently bounds-checked
    # by apci.PropertyValueRead.to_knx(), but only per-chunk - a count large
    # enough to push a later chunk's start_index past 0xFFF would otherwise
    # only fail mid-transfer, after earlier chunks already went out.
    if start_index + count - 1 > 0xFFF:
        raise ValueError(
            f"start_index + count - 1 must be <= {0xFFF}, got {start_index + count - 1}"
        )

    data = bytearray()
    remaining = count
    current_index = start_index
    # First request: read exactly 1 element - the only size that's safe to
    # ask for without already knowing element_size. Widened once that
    # response reveals it.
    max_elements_per_chunk = 1
    element_size: int | None = None

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

        if element_size is None:
            # This is always the 1-element probe request (response_count == 1,
            # guaranteed by the check above), so its data length *is* the
            # element size directly - no division needed.
            element_size = len(response.payload.data)
            if element_size == 0:
                raise ManagementConnectionError(
                    f"Property read failed: object {object_index} PID {property_id} "
                    f"index {current_index} returned empty data for 1 element"
                )
            max_elements_per_chunk = min(
                MAX_ELEMENTS_PER_REQUEST,
                max(
                    1, (max_apdu_length - PROPERTY_VALUE_HEADER_OCTETS) // element_size
                ),
            )

        data.extend(response.payload.data)
        current_index += response_count
        remaining -= response_count

    return bytes(data)
