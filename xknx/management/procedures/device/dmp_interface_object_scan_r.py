"""DMP_InterfaceObjectScan_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.28.2."""

from __future__ import annotations

from dataclasses import dataclass, field

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceGenericPropertyId
from xknx.telegram import apci

__all__ = ["ScannedInterfaceObject", "dmp_interface_object_scan_r"]

# object_index and property_index are single-octet fields (KNX v02.01.01 -
# Application Layer 03.03.07 - §3.4.3.1 A_PropertyDescription_Read-PDU)
MAX_INDEX = 0xFF


@dataclass
class ScannedInterfaceObject:
    """An interface object discovered by DMP_InterfaceObjectScan_R."""

    object_index: int
    object_type: int
    properties: list[apci.PropertyDescriptionResponse] = field(default_factory=list)


async def dmp_interface_object_scan_r(
    conn: P2PConnection,
) -> list[ScannedInterfaceObject]:
    """
    Enumerate all interface objects and their properties on a device.

    DMP_InterfaceObjectScan_R — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.28.2. Requires an established connection (DM_Connect must be executed
    first).

    :param conn: Active P2P connection to the device
    :return: List of discovered interface objects with their property descriptions
    :raises ManagementConnectionError: On disconnect or missing object type data
    """
    objects: list[ScannedInterfaceObject] = []
    object_index = 0

    while True:
        if object_index > MAX_INDEX:
            raise ManagementConnectionError(
                f"No end of interface object list (PID=0) within {MAX_INDEX + 1} objects"
            )
        # Check if an interface object exists at this index (PID=0 → use property_index)
        exist_resp = await conn.request(
            payload=apci.PropertyDescriptionRead(
                object_index=object_index,
                property_id=0,
                property_index=0,
            ),
            expected=apci.PropertyDescriptionResponse,
        )
        # `expected` guarantees this via `P2PConnection._receive`
        assert isinstance(exist_resp.payload, apci.PropertyDescriptionResponse)
        if exist_resp.payload.property_id == 0:
            break  # no more objects

        # Read the object type - KNX v02.01.01 - Application Interface Layer
        # 03.04.01 - §4.3.2.3: PID_OBJECT_TYPE is always property_id 1,
        # mandatory for every Interface Object. Per KNX v02.01.02 -
        # Management Procedures 03.05.02 - §3.28.2, only its first element
        # (start_index=1) is read here - PID_OBJECT_TYPE can itself be an
        # array for array Interface Objects, but the type only needs element 1.
        type_resp = await conn.request(
            payload=apci.PropertyValueRead(
                object_index=object_index,
                property_id=ResourceGenericPropertyId.PID_OBJECT_TYPE,
                count=1,
                start_index=1,
            ),
            expected=apci.PropertyValueResponse,
        )
        # `expected` guarantees this via `P2PConnection._receive`
        assert isinstance(type_resp.payload, apci.PropertyValueResponse)
        if type_resp.payload.count == 0:
            raise ManagementConnectionError(
                f"Object type read failed for object_index={object_index}: nr_of_elem=0"
            )
        if len(type_resp.payload.data) != 2:
            raise ManagementConnectionError(
                f"Object type read for object_index={object_index} returned "
                f"{len(type_resp.payload.data)} bytes, expected 2"
            )
        object_type = int.from_bytes(type_resp.payload.data, "big")

        # Enumerate all properties of this object
        properties: list[apci.PropertyDescriptionResponse] = []
        property_index = 0
        while True:
            if property_index > MAX_INDEX:
                raise ManagementConnectionError(
                    f"No end of property list (PID=0) for object_index="
                    f"{object_index} within {MAX_INDEX + 1} properties"
                )
            prop_resp = await conn.request(
                payload=apci.PropertyDescriptionRead(
                    object_index=object_index,
                    property_id=0,
                    property_index=property_index,
                ),
                expected=apci.PropertyDescriptionResponse,
            )
            # `expected` guarantees this via `P2PConnection._receive`
            assert isinstance(prop_resp.payload, apci.PropertyDescriptionResponse)
            if prop_resp.payload.property_id == 0:
                break
            properties.append(prop_resp.payload)
            property_index += 1

        objects.append(
            ScannedInterfaceObject(
                object_index=object_index,
                object_type=object_type,
                properties=properties,
            )
        )
        object_index += 1

    return objects
