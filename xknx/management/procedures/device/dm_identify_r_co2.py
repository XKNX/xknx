"""DM_Identify_RCo2 — KNX v02.01.02 - Management Procedures 03.05.02 - §3.4.3."""

from __future__ import annotations

from dataclasses import dataclass

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceDevicePropertyId, ResourceGenericPropertyId

from .dmp_interface_object_read_r import dmp_interface_object_read_r

__all__ = ["DeviceIdentity", "dm_identify_r_co2"]

# PID_MANUFACTURER_ID is PDT_UNSIGNED_INT (16 bit, KNX v01.10.01 -
# Resources 03.05.01 - §4.2.12).
_MANUFACTURER_ID_OCTETS = 2
# PID_HARDWARE_TYPE is PDT_GENERIC_06 (KNX v01.10.01 - Resources 03.05.01 -
# §4.3.28).
_HARDWARE_TYPE_OCTETS = 6


@dataclass(slots=True)
class DeviceIdentity:
    """Result of DM_Identify_RCo2 - a device's Device Descriptor, manufacturer and hardware type."""

    device_descriptor_type_0: int
    manufacturer_id: int
    hardware_type: bytes
    """6 octets, high octet 00h for manufacturer-specific device identification (§4.3.28)."""


async def dm_identify_r_co2(
    conn: P2PConnection, device_descriptor_type_0: int
) -> DeviceIdentity:
    """
    Identify a connected device's manufacturer and hardware type.

    DM_Identify_RCo2 — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.4.3. Requires an established connection (DM_Connect must be executed
    first). ``device_descriptor_type_0`` is not read again here - per the
    spec's own note, "DM_Connect_RCo already returns the value of the
    Device Descriptor Type 0 of the Management Server. This result is part
    of the return of this procedure" - so pass through whatever
    :func:`~.dm_connect_r_co.dmp_connect_r_co` (or
    :func:`~.dm_identify_r.dm_identify_r`) already returned for this
    connection.

    The spec's own exception handling for this procedure goes beyond the
    general case: "[i]f any of these services fails ... then the request
    shall be repeated up to three times" before the procedure is
    interrupted. This implementation does not retry - like every other
    procedure in this package, a failure is raised immediately - since the
    spec does not say whether "up to three times" means three attempts in
    total or three retries after the first failure, and no other procedure
    here has an established retry convention to extend. A caller wanting
    the spec-literal retry behaviour can wrap this call in its own retry
    loop.

    :param conn: Active P2P connection to the device
    :param device_descriptor_type_0: The device's Device Descriptor Type 0,
        already known from this connection's own DM_Connect_RCo
    :return: The device's manufacturer ID and hardware type, alongside the
        given ``device_descriptor_type_0``
    :raises ManagementConnectionError: If either property's response
        doesn't carry the octet count its Property Datatype mandates
    """
    manufacturer_data = await dmp_interface_object_read_r(
        conn,
        object_index=0,
        property_id=ResourceGenericPropertyId.PID_MANUFACTURER_ID,
        count=1,
        start_index=1,
    )
    if len(manufacturer_data) != _MANUFACTURER_ID_OCTETS:
        raise ManagementConnectionError(
            f"PID_MANUFACTURER_ID returned {len(manufacturer_data)} octets, "
            f"expected {_MANUFACTURER_ID_OCTETS}"
        )
    manufacturer_id = int.from_bytes(manufacturer_data, "big")

    hardware_type = await dmp_interface_object_read_r(
        conn,
        object_index=0,
        property_id=ResourceDevicePropertyId.PID_HARDWARE_TYPE,
        count=1,
        start_index=1,
    )
    if len(hardware_type) != _HARDWARE_TYPE_OCTETS:
        raise ManagementConnectionError(
            f"PID_HARDWARE_TYPE returned {len(hardware_type)} octets, "
            f"expected {_HARDWARE_TYPE_OCTETS}"
        )

    return DeviceIdentity(
        device_descriptor_type_0=device_descriptor_type_0,
        manufacturer_id=manufacturer_id,
        hardware_type=hardware_type,
    )
