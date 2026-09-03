"""DM_Restart_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.7.3."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")

# A_Restart_Response error codes (KNX v02.01.01 - Application Layer 03.03.07 -
# §3.4.2.2), as enumerated for DM_Restart_RCo's exception handling (KNX
# v02.01.02 - Management Procedures 03.05.02 - §3.7.3).
_ERROR_CODES = {
    0x01: "Access Denied",
    0x02: "Unsupported Erase Code",
    0x03: "Invalid Channel Number",
}


async def dm_restart_r_co(
    conn: P2PConnection,
    *,
    master_reset: bool = False,
    erase_code: int = 0,
    channel_number: int = 0,
) -> apci.RestartMasterResetResponse | None:
    """
    Restart the device on an already-open connection.

    DM_Restart_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.7.3.
    Covers both a Basic Restart (default) and a Master Reset (``master_reset``);
    they are the same Management Procedure, distinguished by the spec's
    ``mpp_RestartType`` parameter. Per the spec, a Master Reset should only be
    requested of a device confirmed to support it.

    A Basic Restart is not confirmed at the application layer (the request is
    sent without waiting for a response) and this transport-layer connection
    breaks down as a side effect - an explicit ``dmp_disconnect_r_co`` should
    still follow. A Master Reset is confirmed by an A_Restart_Response-PDU
    before the device restarts and tears the connection down the same way.

    :param conn: an established P2P connection to the device
    :param master_reset: if True, request a Master Reset instead of a Basic
        Restart
    :param erase_code: which resource(s) to reset to their default value
        (``mpp_EraseCode``); only meaningful with ``master_reset``
    :param channel_number: the application channel to reset, or 0
        (``mpp_ChannelNumber``); only meaningful with ``master_reset``
    :return: the device's A_Restart_Response (error code and process time) for
        a Master Reset, or None for a Basic Restart (never confirmed)
    :raises ManagementConnectionError: if the device refuses the Master Reset
        (non-zero error code)
    """
    if not master_reset:
        logger.debug("Requesting a Basic Restart of %s.", conn.address)
        await conn.send_data(apci.Restart(), wait_for_ack=False)
        return None

    logger.debug(
        "Requesting a Master Reset of %s (erase code %#04x, channel %d).",
        conn.address,
        erase_code,
        channel_number,
    )
    response = await conn.request(
        apci.RestartMasterReset(erase_code=erase_code, channel_number=channel_number)
    )
    result = response.payload
    if result.error_code != 0:
        reason = _ERROR_CODES.get(result.error_code, "Unknown Error")
        raise ManagementConnectionError(
            f"{conn.address} refused Master Reset (erase code {erase_code:#04x}, "
            f"channel {channel_number}): error code {result.error_code:#04x} "
            f"({reason})"
        )
    return result


async def dm_restart(
    xknx: XKNX,
    individual_address: IndividualAddressableType,
    *,
    master_reset: bool = False,
    erase_code: int = 0,
    channel_number: int = 0,
) -> apci.RestartMasterResetResponse | None:
    """
    Restart a device, opening and closing a connection to it.

    :param xknx: the XKNX object
    :param individual_address: address of the device to restart
    :param master_reset: if True, request a Master Reset instead of a Basic
        Restart
    :param erase_code: which resource(s) to reset to their default value;
        only meaningful with ``master_reset``
    :param channel_number: the application channel to reset, or 0; only
        meaningful with ``master_reset``
    :return: the device's A_Restart_Response for a Master Reset, or None for
        a Basic Restart (never confirmed)
    :raises ManagementConnectionError: if the device refuses the Master Reset
    """
    async with xknx.management.connection(
        IndividualAddress(individual_address)
    ) as conn:
        return await dm_restart_r_co(
            conn,
            master_reset=master_reset,
            erase_code=erase_code,
            channel_number=channel_number,
        )
