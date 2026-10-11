"""DMP_ProgModeSwitch_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.13.2."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.management.management import P2PConnection
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

from .dmp_mem_read_r_co import dmp_mem_read_r_co
from .dmp_mem_write_r_co import dmp_mem_write_r_co

if TYPE_CHECKING:
    from xknx import XKNX

__all__ = ["PROG_MODE_ADDRESS", "dm_prog_mode_switch", "dmp_prog_mode_switch_r_co"]

# Location of curr_prog_mode - KNX v01.10.01 - Resources 03.05.01 - §4.26.3.2.
PROG_MODE_ADDRESS = 0x0060
# prog_mode and p_parity in curr_prog_mode - KNX v01.10.01 - Resources 03.05.01 - §4.26.3.1.
_PROG_MODE_BIT = 0x01
_PARITY_BIT = 0x80


async def dmp_prog_mode_switch_r_co(conn: P2PConnection, mode: bool) -> None:
    r"""
    Switch the Programming Mode of a device on or off.

    DMP_ProgModeSwitch_RCo — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.13.2. Requires an established connection (DM_Connect must be executed
    first). Applies to devices realising the Programming Mode as "Programming
    Mode - Realisation Type 2" (KNX v01.10.01 - Resources 03.05.01 - §4.26.3),
    i.e. in the memory octet ``curr_prog_mode`` at 60h. Devices of Realisation
    Type 1 (§4.26.2) use the Device Object's ``PID_PROGMODE`` instead, e.g.::

        await dmp_interface_object_write_r(
            conn, 0, ResourceDevicePropertyId.PID_PROGMODE, b"\x01"
        )

    ``curr_prog_mode`` is read and written back with ``prog_mode`` (bit 0) set
    according to ``mode``. The shared bits 1 to 6 are kept, and ``p_parity``
    (bit 7) is inverted along with ``prog_mode`` (KNX v01.10.01 - Resources
    03.05.01 - §4.26.3.4.1). If ``prog_mode`` already equals ``mode``, nothing
    is written (KNX v01.10.01 - Resources 03.05.01 - §4.26.3.4.2 and
    §4.26.3.4.3).

    :param conn: Active P2P connection to the device
    :param mode: True to switch the Programming Mode on, False to switch it off
    :raises ManagementConnectionError: If the device answers the read with no
        data, or with a different address
    """
    (value,) = await dmp_mem_read_r_co(conn, address=PROG_MODE_ADDRESS, size=1)
    # Already in the requested mode: leave curr_prog_mode untouched.
    if bool(value & _PROG_MODE_BIT) == mode:
        return
    value ^= _PROG_MODE_BIT | _PARITY_BIT
    await dmp_mem_write_r_co(conn, address=PROG_MODE_ADDRESS, data=bytes([value]))


async def dm_prog_mode_switch(
    xknx: XKNX,
    individual_address: IndividualAddressableType,
    mode: bool,
) -> None:
    """
    Switch the Programming Mode of a device, opening and closing a connection to it.

    Connects, switches and disconnects as in KNX v01.10.01 - Resources
    03.05.01 - §4.26.3.4.2 and §4.26.3.4.3. See
    :func:`dmp_prog_mode_switch_r_co` for which devices this applies to.

    :param xknx: the XKNX object
    :param individual_address: address of the device
    :param mode: True to switch the Programming Mode on, False to switch it off
    :raises ManagementConnectionError: If the device answers the read with no
        data, or with a different address
    """
    async with xknx.management.connection(
        IndividualAddress(individual_address)
    ) as conn:
        await dmp_prog_mode_switch_r_co(conn, mode)
