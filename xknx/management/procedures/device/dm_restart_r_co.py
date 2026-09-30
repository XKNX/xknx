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

# Erase Codes valid for a Master Reset (KNX v02.01.02 - Management Procedures
# 03.05.02 - §3.7.1.2.3.1, Table 4). 00h and 09h-FFh are reserved and the
# spec is explicit that "The Management Client shall not use these Erase
# Codes" - a device receiving one must refuse with error code 02h without
# acting, so sending one can never succeed.
_MIN_ERASE_CODE = 0x01
_MAX_ERASE_CODE = 0x08
# 01h "Confirmed Restart": resets nothing, only gives a Basic Restart an
# application-layer confirmation - the least destructive Erase Code and the
# spec's own suggested substitute for an unconfirmed Basic Restart.
_CONFIRMED_RESTART_ERASE_CODE = 0x01

# A_Restart_Response error codes (KNX v02.01.02 - Management Procedures
# 03.05.02 - §3.7.1.2.3.1, Table 5).
_ERROR_CODES = {
    0x01: "Access denied",
    0x02: "Unsupported Erase Code",
    0x03: "Invalid Channel Number",
}


async def dm_restart_r_co(
    conn: P2PConnection,
    *,
    master_reset: bool = False,
    erase_code: int = _CONFIRMED_RESTART_ERASE_CODE,
    channel_number: int = 0,
) -> apci.RestartMasterResetResponse | None:
    """
    Restart the device on an already-open connection.

    DM_Restart_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.7.3.
    Covers both a Basic Restart (default) and a Master Reset (``master_reset``);
    they are the same Management Procedure, distinguished by the spec's
    ``mpp_RestartType`` parameter. Per the spec, a Master Reset should only be
    requested of a device confirmed to support it - footnote 11 notes that an
    existing implementation may instead ignore the service, or perform a
    Basic Restart and drop the connection, in which case ``conn.request()``
    below times out with ``ManagementConnectionTimeout`` rather than raising
    the ``ManagementConnectionError`` a spec-conformant refusal would.

    A Basic Restart is not confirmed at the application layer (the request is
    sent without waiting for a response) and this transport-layer connection
    breaks down as a side effect - an explicit ``dmp_disconnect_r_co`` should
    still follow. A Master Reset is confirmed by an A_Restart_Response-PDU
    before the device restarts and tears the connection down the same way.

    :param conn: an established P2P connection to the device
    :param master_reset: if True, request a Master Reset instead of a Basic
        Restart
    :param erase_code: which resource(s) to reset to their default value
        (``mpp_EraseCode``); only meaningful with ``master_reset``. Must be
        01h-08h (KNX v02.01.02 - Management Procedures 03.05.02 - §3.7.1.2.3.1,
        Table 4) - 00h and 09h-FFh are reserved values a Management Client
        must not send. Defaults to 01h "Confirmed Restart", which resets
        nothing and only adds the application-layer confirmation a Basic
        Restart lacks.
    :param channel_number: the application channel to reset, or 0
        (``mpp_ChannelNumber``); only meaningful with ``master_reset``
    :return: the device's A_Restart_Response for a Master Reset, or None for
        a Basic Restart (never confirmed). The response's ``process_time`` is
        not just informational: the spec requires the Management Client to
        treat it as "time-out after which communication attempts following a
        Master Reset shall be considered without success" - i.e. the
        mandated minimum wait before retrying.
    :raises ValueError: if ``master_reset`` is set and ``erase_code`` is
        outside 01h-08h
    :raises ManagementConnectionError: if the device refuses the Master Reset
        (non-zero error code)
    """
    if not master_reset:
        logger.debug("Requesting a Basic Restart of %s.", conn.address)
        await conn.send_data(apci.Restart(), wait_for_ack=False)
        return None

    if not _MIN_ERASE_CODE <= erase_code <= _MAX_ERASE_CODE:
        raise ValueError(
            f"erase_code must be {_MIN_ERASE_CODE:#04x}-{_MAX_ERASE_CODE:#04x} for "
            f"a Master Reset (KNX v02.01.02 - Management Procedures 03.05.02 - "
            f"§3.7.1.2.3.1, Table 4 - other values are reserved and a "
            f"Management Client shall not send them), got {erase_code:#04x}"
        )

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
    erase_code: int = _CONFIRMED_RESTART_ERASE_CODE,
    channel_number: int = 0,
) -> apci.RestartMasterResetResponse | None:
    """
    Restart a device, opening and closing a connection to it.

    :param xknx: the XKNX object
    :param individual_address: address of the device to restart
    :param master_reset: if True, request a Master Reset instead of a Basic
        Restart
    :param erase_code: which resource(s) to reset to their default value;
        only meaningful with ``master_reset``. Must be 01h-08h - see
        :func:`dm_restart_r_co` for the full range and default rationale.
    :param channel_number: the application channel to reset, or 0; only
        meaningful with ``master_reset``
    :return: the device's A_Restart_Response for a Master Reset, or None for
        a Basic Restart (never confirmed). See :func:`dm_restart_r_co` for
        what ``process_time`` obligates the caller to do.
    :raises ValueError: if ``master_reset`` is set and ``erase_code`` is
        outside 01h-08h
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
