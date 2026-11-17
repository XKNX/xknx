"""DMP_ProgModeSwitch_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.13.2."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.management.management import P2PConnection
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

from .dm_connect_r_co import dmp_connect_r_co
from .dmp_mem_read_r_co import dmp_mem_read_r_co
from .dmp_mem_write_r_co import dmp_mem_write_r_co

if TYPE_CHECKING:
    from xknx import XKNX

__all__ = [
    "dm_prog_mode_switch",
    "dmp_prog_mode_switch_r_co",
]

# Location of curr_prog_mode - KNX v01.10.01 - Resources 03.05.01 - §4.26.3.2.
_PROG_MODE_ADDRESS = 0x0060
# prog_mode and p_parity in curr_prog_mode - KNX v01.10.01 - Resources 03.05.01 - §4.26.3.1.
_PROG_MODE_BIT = 0x01
_PARITY_BIT = 0x80


async def dmp_prog_mode_switch_r_co(
    conn: P2PConnection, mode: bool, verify: bool = False
) -> None:
    """
    Switch the Programming Mode of a device on or off.

    DMP_ProgModeSwitch_RCo — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.13.2. Requires an established connection (DM_Connect must be executed
    first). Applies to devices realising the Programming Mode as "Programming
    Mode - Realisation Type 2" (KNX v01.10.01 - Resources 03.05.01 - §4.26.3),
    i.e. in the memory octet ``curr_prog_mode`` at 60h. Devices of Realisation
    Type 1 (§4.26.2) use the Device Object's ``PID_PROGMODE`` instead
    (:func:`prog_mode_property_switch_conn`); :func:`prog_mode_switch` picks
    the right one by the device's mask version.

    ``curr_prog_mode`` is read and written back with ``prog_mode`` (bit 0) set
    according to ``mode``. The shared bits 1 to 6 are kept, and ``p_parity``
    (bit 7) is inverted along with ``prog_mode`` (KNX v01.10.01 - Resources
    03.05.01 - §4.26.3.4.1). If ``prog_mode`` already equals ``mode``, nothing
    is written (KNX v01.10.01 - Resources 03.05.01 - §4.26.3.4.2 and
    §4.26.3.4.3).

    A_Memory_Write is not confirmed at the application layer, so a device that
    rejects the write (e.g. access protection) goes unnoticed unless
    ``verify`` reads ``curr_prog_mode`` back. §3.13.2 does not ask for this
    read-back.

    :param conn: Active P2P connection to the device
    :param mode: True to switch the Programming Mode on, False to switch it off
    :param verify: If True, read ``curr_prog_mode`` back after writing it
    :raises ManagementConnectionError: If the device answers a read with no
        data, or with a different address
    :raises VerificationError: If verify is enabled and the read-back does not
        match what was written
    """
    (value,) = await dmp_mem_read_r_co(conn, address=_PROG_MODE_ADDRESS, size=1)
    # Already in the requested mode: leave curr_prog_mode untouched.
    if bool(value & _PROG_MODE_BIT) == mode:
        return
    value ^= _PROG_MODE_BIT | _PARITY_BIT
    await dmp_mem_write_r_co(
        conn, address=_PROG_MODE_ADDRESS, data=bytes([value]), verify=verify
    )


async def dm_prog_mode_switch(
    xknx: XKNX,
    individual_address: IndividualAddressableType,
    mode: bool,
    verify: bool = False,
) -> None:
    """
    Switch the Programming Mode of a device, opening and closing a connection to it.

    DM_ProgMode_Switch - KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.13: connects, executes DM_Connect (§3.13.1), switches ``curr_prog_mode``
    at memory 60h with :func:`dmp_prog_mode_switch_r_co` and disconnects, as in
    KNX v01.10.01 - Resources 03.05.01 - §4.26.3.4.2 and §4.26.3.4.3. The mask
    version read by DM_Connect is not checked: for a device whose Programming
    Mode may be elsewhere, use :func:`prog_mode_switch`.

    :param xknx: the XKNX object
    :param individual_address: address of the device
    :param mode: True to switch the Programming Mode on, False to switch it off
    :param verify: If True, read ``curr_prog_mode`` back after writing it
    :raises ManagementConnectionError: If the device answers a read with no
        data, or with a different address
    :raises VerificationError: If verify is enabled and the read-back does not
        match what was written
    """
    async with xknx.management.connection(
        IndividualAddress(individual_address)
    ) as conn:
        await dmp_connect_r_co(conn)
        await dmp_prog_mode_switch_r_co(conn, mode, verify=verify)
