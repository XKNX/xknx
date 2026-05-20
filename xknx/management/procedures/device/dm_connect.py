"""DM_Connect — KNX 03.05.02 §3.2.1 (PDF p. 67)."""

from __future__ import annotations

from xknx.management.protocols import P2PConnection
from xknx.telegram import apci

__all__ = ["dm_connect"]


async def dm_connect(conn: P2PConnection) -> int:
    """
    Confirm an open P2P connection by reading the device descriptor (DD0).

    DMP_Connect_RCo — KNX 03.05.02 §3.2.1. The transport-layer connection
    must already be established. Returns the mask version (DD0 value).

    :param conn: an established P2P connection to the device
    :return: Device Descriptor Type 0 value (mask version, 2 bytes)
    """
    response = await conn.request(
        payload=apci.DeviceDescriptorRead(descriptor=0),
        expected=apci.DeviceDescriptorResponse,
    )
    return response.payload.value
