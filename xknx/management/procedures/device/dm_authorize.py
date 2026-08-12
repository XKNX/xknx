"""DM_Authorize — KNX v02.01.02 - Management Procedures 03.05.02 - §3.5."""

from __future__ import annotations

from xknx.management.management import P2PConnection
from xknx.telegram import apci

FREE_ACCESS_KEY = 0xFFFFFFFF

__all__ = ["FREE_ACCESS_KEY", "dmp_authorize2_r_co", "dmp_authorize_r_co"]


async def dmp_authorize_r_co(conn: P2PConnection, key: int) -> int:
    """
    Authorize with a KNX device to obtain access rights.

    DMP_Authorize_RCo — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.5.1. Requires an established connection (DM_Connect must be
    executed first). Per spec, authorization is only required (and this
    should only be called) when `key` isn't FREE_ACCESS_KEY - sending a
    request with that key anyway needlessly risks a timeout against a
    device that doesn't implement A_Authorize at all.

    :param conn: Active P2P connection to the device
    :param key: 4-byte authorization key
    :return: Access level granted by the device (0 = highest, 15 = lowest)
    """
    response = await conn.request(
        payload=apci.AuthorizeRequest(key=key),
        expected=apci.AuthorizeResponse,
    )
    # `expected` guarantees this via `P2PConnection._receive`
    assert isinstance(response.payload, apci.AuthorizeResponse)
    return response.payload.level


async def dmp_authorize2_r_co(conn: P2PConnection, client_key: int) -> int:
    """
    Authorize with a KNX device, comparing free access vs client key.

    DMP_Authorize2_RCo — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.5.2. Tries free access first, then client key, and uses whichever
    gives better (lower) access level.

    :param conn: Active P2P connection to the device
    :param client_key: 4-byte client authorization key
    :return: Best access level obtained (0 = highest, 15 = lowest)
    """
    free_level = await dmp_authorize_r_co(conn, FREE_ACCESS_KEY)

    if free_level == 0:
        return free_level

    client_level = await dmp_authorize_r_co(conn, client_key)

    if client_level > free_level:
        return await dmp_authorize_r_co(conn, FREE_ACCESS_KEY)

    return client_level
