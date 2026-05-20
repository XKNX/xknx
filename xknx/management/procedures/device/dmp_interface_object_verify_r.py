"""
DMP_InterfaceObjectVerify_R — KNX 03.05.02 §3.26.2 (PDF p. 120).

Spec text (verbatim from spec):

    This Management Procedure shall use the connection oriented or connectionless communication
    mode.

    Used Application Layer Services for Management
    - A_PropertyDescription_Read
    - A_PropertyValue_Read

    Sequence

    ```mermaid
    sequenceDiagram
        participant C as Management Client
        participant S as Management Server
        opt Property of management control is unknown to the Management Client
            C->>S: A_PropertyDescription_Read-PDU (object_index = OO, PID = PP)
            S->>C: A_PropertyDescription_Response-PDU (object_index = OO, PID = PP, type = .. , ...)
            Note right of S: A_Disconnect.ind ⇒ error, Property does not exist ⇒ error
        end
        loop for each data block, until all data are transmitted
            C->>S: A_PropertyValue_Read-PDU (object_index = OO, PID = PP, start_index = SSSS, element_count = EE)
            S->>C: A_PropertyValue_Response-PDU (object_index = OO, PID = PP, start_index = SSSS, element_count = EE, data = XX, ..)
            Note right of S: A_Disconnect.ind ⇒ error, different or no data received ⇒ error
        end
    ```

    Exception handling
    The general exception handling shall apply.
    The Management Client shall not interpret the value of the Property Index contained in the
    A_PropertyDescription_Response-PDU at the level of this Management Procedure. Possibly, error
    handling in case an unexpected value of the Property Index can be handled at the level of the
    Configuration Procedure in which this Management Procedure is used.

Inputs (from spec):
    (see body)
"""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.management.protocols import P2PConnection
from xknx.telegram import apci

# nr_of_elem field is 4 bits (KNX 03.03.07 v02.01.01 §3.4.4 Figure 46), max value 2^4 - 1
MAX_ELEMENTS_PER_REQUEST = (1 << 4) - 1


async def dmp_interface_object_verify_r(
    connection: P2PConnection,
    object_index: int,
    property_id: int,
    expected_data: bytes,
    count: int = 1,
    start_index: int = 1,
) -> None:
    """
    Verify that a device's property value matches expected data, block by block.

    DMP_InterfaceObjectVerify_R — KNX 03.05.02 §3.26.2. Requires an established
    connection (DM_Connect must be executed first). Per-block comparison satisfies
    the spec's "different or no data received ⇒ error" note inside the loop.

    :param connection: Active P2P connection to the device
    :param object_index: Index of the interface object (0-255)
    :param property_id: Property identifier (1-255)
    :param expected_data: Data the property is expected to contain
    :param count: Number of elements to verify
    :param start_index: Start element index (1-based, 1-4095)
    :raises ManagementConnectionError: If any block read fails or does not match expected
    :raises ValueError: If expected_data length is not divisible by count
    """
    if count <= 0:
        return

    if len(expected_data) % count != 0:
        raise ValueError(
            f"expected_data length {len(expected_data)} must be divisible by element count {count}"
        )

    # The spec's sequence (A_PropertyDescription_Read) is intentionally skipped:
    # callers supply object_index/property_id/count/start_index explicitly, so the
    # property is always known at this level. Discovery belongs to the Configuration
    # Procedure above (per spec: "shall not interpret ... at the level of this
    # Management Procedure"). Use dmp_interface_object_scan_r to discover properties
    # (type, max_count, access) before calling this function.
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

        response = await connection.request(
            payload=apci.PropertyValueRead(
                object_index=object_index,
                property_id=property_id,
                count=chunk_count,
                start_index=current_index,
            ),
            expected=apci.PropertyValueResponse,
        )

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
            raise ManagementConnectionError(
                f"Property verify failed: object {object_index} PID {property_id} "
                f"index {current_index}: expected {expected_chunk.hex()}, "
                f"got {response.payload.data.hex()}"
            )

        current_index += response_count
        remaining -= response_count
        data_offset += response_count * element_size
