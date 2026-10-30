"""DM_SecureSync_RCl — KNX v02.01.02 - Management Procedures 03.05.02 - §4.2."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from xknx.exceptions import DataSecureError, ManagementConnectionTimeout
from xknx.management.management import P2PConnection
from xknx.telegram.address import IndividualAddress, IndividualAddressableType
from xknx.telegram.apci import SecureAPDU

if TYPE_CHECKING:
    from xknx import XKNX

logger = logging.getLogger("xknx.management.procedures")

# "If the MaC does not receive a response from the MaS, then it shall repeat the
# request once." - KNX v02.01.02 - Management Procedures 03.05.02 - §4.1
_ATTEMPTS = 2


async def dm_secure_sync_r_cl(
    xknx: XKNX,
    individual_address: IndividualAddressableType,
    *,
    serial_number: bytes | None = None,
) -> None:
    """
    Synchronize the Sequence Numbers for Tool Access with a device.

    Opens and closes its own connection; see `dm_secure_sync_r_cl_conn`.
    """
    async with xknx.management.connection(
        address=IndividualAddress(individual_address)
    ) as connection:
        await dm_secure_sync_r_cl_conn(connection, serial_number=serial_number)


async def dm_secure_sync_r_cl_conn(
    conn: P2PConnection,
    *,
    serial_number: bytes | None = None,
) -> None:
    """
    Synchronize the Sequence Numbers for Tool Access on an already-open connection.

    DM_SecureSync_RCl — KNX v02.01.02 - Management Procedures 03.05.02 - §4.2,
    connection-oriented, with the Tool Access flag set: the S-A_Sync_Req-PDU is secured
    with the Tool Key of the device (its FDSK while it is in its delivery state) that
    was given to `DataSecure.set_tool_key()`. The device answers with its own Sequence
    Number Sending and the one it expects from us; afterwards the frames to and from
    the device on this and later connections are secured with the Tool Key -
    KNX v02.01.01 - Application Layer 03.03.07 - §5.3.2.

    A device ignores a request within 1 s after it answered one, and does not answer
    a request it cannot verify (e.g. a wrong key) at all.

    :param conn: an established P2P connection to the device
    :param serial_number: the assumed KNX Serial Number of the device (6 octets) or
        None to send 0, which every device accepts on point-to-point
    :raises DataSecureError: if no Data Secure or no Tool Key for the device is set up
    :raises ManagementConnectionTimeout: if the device does not answer the request
        and its repetition
    """
    data_secure = conn.xknx.cemi_handler.data_secure
    if data_secure is None:
        raise DataSecureError("Data Secure is not initialized")
    for attempt in range(_ATTEMPTS):
        request = data_secure.sync_request(conn.address, serial_number=serial_number)
        try:
            response = await conn.request(request)
        except ManagementConnectionTimeout:
            logger.debug(
                "No S-A_Sync response from %s (attempt %s of %s)",
                conn.address,
                attempt + 1,
                _ATTEMPTS,
            )
            continue
        if isinstance(response.payload, SecureAPDU) and (
            data_secure.tool_access_synchronized(conn.address)
        ):
            return
    raise ManagementConnectionTimeout(
        f"No S-A_Sync response from {conn.address} - wrong Tool Key?"
    )
