"""DM_Identify_RCo2 — KNX v02.01.02 - Management Procedures 03.05.02 - §3.4.3."""

from __future__ import annotations

from dataclasses import dataclass

from xknx.exceptions import ManagementConnectionError, ManagementConnectionRefused
from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceDevicePropertyId, ResourceGenericPropertyId

from .dm_connect_r_co import dmp_connect_r_co
from .dmp_interface_object_read_r import dmp_interface_object_read_r

__all__ = ["DeviceIdentity", "dm_identify_r_co2"]

# PID_MANUFACTURER_ID is PDT_UNSIGNED_INT (16 bit, KNX v01.10.01 -
# Resources 03.05.01 - §4.2.12).
_MANUFACTURER_ID_OCTETS = 2
# PID_HARDWARE_TYPE is PDT_GENERIC_06 (KNX v01.10.01 - Resources 03.05.01 -
# §4.3.28).
_HARDWARE_TYPE_OCTETS = 6
# KNX v02.01.02 - Management Procedures 03.05.02 - §3.4.3: "If any of these
# services fails (time-out, negative response, no response) then the
# request shall be repeated up to three times."
_DEFAULT_RETRIES = 3


@dataclass(slots=True)
class DeviceIdentity:
    """Result of DM_Identify_RCo2 - a device's Device Descriptor, manufacturer and hardware type."""

    device_descriptor_type_0: int
    manufacturer_id: int
    hardware_type: bytes
    """6 octets, high octet 00h for manufacturer-specific device identification (§4.3.28)."""


async def dm_identify_r_co2(
    conn: P2PConnection,
    device_descriptor_type_0: int | None = None,
    *,
    retries: int = _DEFAULT_RETRIES,
) -> DeviceIdentity:
    """
    Identify a connected device's manufacturer and hardware type.

    DM_Identify_RCo2 — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.4.3. Uses the connection-oriented mode over an open
    ``P2PConnection``. "DM_Connect_RCo already returns the value of the
    Device Descriptor Type 0 of the Management Server. This result is part
    of the return of this procedure" - pass what
    :func:`~.dm_connect_r_co.dmp_connect_r_co` (or
    :func:`~.dm_identify_r.dm_identify_r`) already returned for this
    connection as ``device_descriptor_type_0``; if it's omitted,
    ``dmp_connect_r_co`` is run here first.

    "If any of these services fails (time-out, negative response, no
    response) then the request shall be repeated up to three times. On
    further failure, the Management Procedure ... shall be interrupted" -
    each property read is attempted once and repeated up to ``retries``
    times on a timeout or negative response. A response with the wrong
    length, or a connection closed by the device, isn't retried.

    :param conn: Active P2P connection to the device
    :param device_descriptor_type_0: The device's Device Descriptor Type 0,
        if already known from this connection's own DM_Connect_RCo
    :param retries: How often a failed property read is repeated
    :return: The device's manufacturer ID and hardware type, alongside its
        Device Descriptor Type 0
    :raises ValueError: If ``retries`` is negative
    :raises ManagementConnectionError: If a property read still fails after
        ``retries`` repeats, or either property's response doesn't carry the
        octet count its Property Datatype mandates
    """
    if retries < 0:
        raise ValueError(f"retries must be >= 0, got {retries}")
    if device_descriptor_type_0 is None:
        device_descriptor_type_0 = await dmp_connect_r_co(conn)

    manufacturer_data = await _read_with_retries(
        conn, ResourceGenericPropertyId.PID_MANUFACTURER_ID, retries
    )
    if len(manufacturer_data) != _MANUFACTURER_ID_OCTETS:
        raise ManagementConnectionError(
            f"PID_MANUFACTURER_ID returned {len(manufacturer_data)} octets, "
            f"expected {_MANUFACTURER_ID_OCTETS}"
        )
    manufacturer_id = int.from_bytes(manufacturer_data, "big")

    hardware_type = await _read_with_retries(
        conn, ResourceDevicePropertyId.PID_HARDWARE_TYPE, retries
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


async def _read_with_retries(
    conn: P2PConnection, property_id: int, retries: int
) -> bytes:
    """Read a device object property, repeating it up to ``retries`` times on failure."""
    attempt = 0
    while True:
        try:
            return await dmp_interface_object_read_r(
                conn,
                object_index=0,
                property_id=property_id,
                count=1,
                start_index=1,
            )
        except ManagementConnectionRefused:
            raise
        except ManagementConnectionError:
            if attempt >= retries:
                raise
            attempt += 1
