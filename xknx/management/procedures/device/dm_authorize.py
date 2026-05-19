"""
DM_Authorize — KNX 03.05.02 §3.5 (PDF p. 74).
"""

from __future__ import annotations

from xknx.management.protocols import P2PConnection
from xknx.telegram import apci

FREE_ACCESS_KEY = 0xFFFFFFFF

__all__ = ["FREE_ACCESS_KEY", "dmp_authorize2_r_co", "dmp_authorize_r_co"]


async def dmp_authorize_r_co(connection: P2PConnection, key: int) -> int:
    """
    Authorize with a KNX device to obtain access rights.

    DMP_Authorize_RCo — KNX 03.05.02 §3.5.1. Requires an established
    connection (DM_Connect must be executed first).

    :param connection: Active P2P connection to the device
    :param key: 4-byte authorization key (0xFFFFFFFF for free access)
    :return: Access level granted by the device (0 = highest, 15 = lowest)
    """
    response = await connection.request(
        payload=apci.AuthorizeRequest(key=key),
        expected=apci.AuthorizeResponse,
    )
    return response.payload.level


async def dmp_authorize2_r_co(connection: P2PConnection, client_key: int) -> int:
    """
    Authorize with a KNX device, comparing free access vs client key.

    DMP_Authorize2_RCo — KNX 03.05.02 §3.5.2. Tries free access first,
    then client key, and uses whichever gives better (lower) access level.

    :param connection: Active P2P connection to the device
    :param client_key: 4-byte client authorization key
    :return: Best access level obtained (0 = highest, 15 = lowest)
    """
    free_level = await dmp_authorize_r_co(connection, FREE_ACCESS_KEY)

    if free_level == 0:
        return free_level

    client_level = await dmp_authorize_r_co(connection, client_key)

    if client_level > free_level:
        await dmp_authorize_r_co(connection, FREE_ACCESS_KEY)
        return free_level

    return client_level
