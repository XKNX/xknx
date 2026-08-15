"""DMP_InterfaceObjectScan_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.28.2."""

from __future__ import annotations

from dataclasses import dataclass, field

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

# KNX v02.01.01 - Application Interface Layer 03.04.01 - §4.3.2.3: the
# Property with property_id = 1 is always PID_OBJECT_TYPE
_PID_OBJECT_TYPE = 0x01


@dataclass
class ScannedInterfaceObject:
    """An interface object discovered by DMP_InterfaceObjectScan_R."""

    object_index: int
    object_type: int
    properties: list[apci.PropertyDescriptionResponse] = field(default_factory=list)


async def dmp_interface_object_scan_r(
    connection: P2PConnection,
) -> list[ScannedInterfaceObject]:
    """
    Enumerate all interface objects and their properties on a device.

    DMP_InterfaceObjectScan_R — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.28.2. Requires an established connection (DM_Connect must be executed
    first).

    :param connection: Active P2P connection to the device
    :return: List of discovered interface objects with their property descriptions
    :raises ManagementConnectionError: On disconnect or missing object type data
    """
    objects: list[ScannedInterfaceObject] = []
    object_index = 0

    while True:
        # Check if an interface object exists at this index (PID=0 → use property_index)
        exist_resp = await connection.request(
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

        # Read the object type (PID_OBJECT_TYPE = 0x01, always 1 element, 2 bytes)
        type_resp = await connection.request(
            payload=apci.PropertyValueRead(
                object_index=object_index,
                property_id=_PID_OBJECT_TYPE,
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
        object_type = int.from_bytes(type_resp.payload.data, "big")

        # Enumerate all properties of this object
        properties: list[apci.PropertyDescriptionResponse] = []
        property_index = 0
        while True:
            prop_resp = await connection.request(
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
