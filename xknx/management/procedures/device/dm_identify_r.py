"""DM_Identify_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.4.2."""

from __future__ import annotations

from dataclasses import dataclass

from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceDevicePropertyId

from .dm_connect_r_co import dmp_connect_r_co
from .dmp_interface_object_read_r import dmp_interface_object_read_r

__all__ = ["IdentifiedDevice", "dm_identify_r"]

# KNX v02.01.02 - Management Procedures 03.05.02 - §3.4.2: devices
# identified by this procedure's second step report Device Descriptor Type
# 0 = 0300h.
_MGT_MODEL_DD0 = 0x0300


@dataclass(slots=True)
class IdentifiedDevice:
    """Result of DM_Identify_R - a device's Device Descriptor and, if applicable, its management model."""

    device_descriptor_type_0: int

    management_model: bytes | None
    """
    ``PID_MGT_DESCRIPTOR_01`` (10 octets), if ``device_descriptor_type_0``
    is 0300h - ``None`` for any other Device Descriptor value, since the
    spec's own step 2 only applies to that one. §3.4.2 calls out two known
    values, ``01000000000000000000h`` and ``01000001000000000000h``, as
    identifying "the specified management model" - any other value is
    returned as-is, uninterpreted, for the caller to match against its own
    profile knowledge.
    """


async def dm_identify_r(conn: P2PConnection) -> IdentifiedDevice:
    """
    Identify a device by its Device Descriptor and, for one legacy type, its management model.

    DM_Identify_R — KNX v02.01.02 - Management Procedures 03.05.02 - §3.4.2.
    Requires an established connection (DM_Connect must be executed first;
    step 1 of this procedure is exactly
    :func:`~.dm_connect_r_co.dmp_connect_r_co`, reused here rather than
    repeating its own ``A_DeviceDescriptor_Read``).

    Step 2 - reading ``PID_MGT_DESCRIPTOR_01`` - only applies to devices
    reporting Device Descriptor Type 0 = 0300h ("continue with identified
    management" otherwise, i.e. skip it); every other Device Descriptor
    value is returned with ``management_model=None``.

    :param conn: Active P2P connection to the device
    :return: The device's Device Descriptor Type 0 and, if applicable, its
        management model
    :raises ManagementConnectionError: If the device does not respond with
        Device Descriptor Type 0, or (when applicable) step 2's response
        carries an unexpected element count
    """
    device_descriptor_type_0 = await dmp_connect_r_co(conn)
    if device_descriptor_type_0 != _MGT_MODEL_DD0:
        return IdentifiedDevice(
            device_descriptor_type_0=device_descriptor_type_0, management_model=None
        )

    management_model = await dmp_interface_object_read_r(
        conn,
        object_index=0,
        property_id=ResourceDevicePropertyId.PID_MGT_DESCRIPTOR_01,
        count=1,
        start_index=1,
    )
    return IdentifiedDevice(
        device_descriptor_type_0=device_descriptor_type_0,
        management_model=management_model,
    )
