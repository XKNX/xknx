"""DMP_ProgModeSwitch_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.13.2."""

from __future__ import annotations

from xknx.management.management import P2PConnection

from .dmp_mem_read_r_co import dmp_mem_read_r_co
from .dmp_mem_write_r_co import dmp_mem_write_r_co

__all__ = ["PROG_MODE_ADDRESS", "dmp_prog_mode_switch_r_co"]

# Location of curr_prog_mode - KNX v01.10.01 - Resources 03.05.01 - §4.26.3.2.
PROG_MODE_ADDRESS = 0x0060
# prog_mode and p_parity in curr_prog_mode - KNX v01.10.01 - Resources 03.05.01 - §4.26.3.1.
_PROG_MODE_BIT = 0x01
_PARITY_BIT = 0x80


async def dmp_prog_mode_switch_r_co(conn: P2PConnection, mode: bool) -> None:
    """
    Switch the Programming Mode of a device on or off.

    DMP_ProgModeSwitch_RCo — KNX v02.01.02 - Management Procedures 03.05.02 -
    §3.13.2. Requires an established connection (DM_Connect must be executed
    first). Applies to devices realising the Programming Mode as "Programming
    Mode - Realisation Type 2" (KNX v01.10.01 - Resources 03.05.01 - §4.26.3),
    i.e. in the memory octet ``curr_prog_mode`` at 60h; devices of Realisation
    Type 1 use the Device Object's ``PID_PROGMODE`` instead (§4.26.2).

    ``curr_prog_mode`` is read and written back with ``prog_mode`` (bit 0) set
    according to ``mode``. The shared bits 1 to 6 are kept, and ``p_parity``
    (bit 7) is inverted whenever ``prog_mode`` changes, so the parity of the
    octet stays valid (KNX v01.10.01 - Resources 03.05.01 - §4.26.3.4.1).

    :param conn: Active P2P connection to the device
    :param mode: True to switch the Programming Mode on, False to switch it off
    :raises ManagementConnectionError: If the device answers the read with no
        data, or with a different address
    """
    (value,) = await dmp_mem_read_r_co(conn, address=PROG_MODE_ADDRESS, size=1)
    if bool(value & _PROG_MODE_BIT) != mode:
        value ^= _PROG_MODE_BIT | _PARITY_BIT
    await dmp_mem_write_r_co(conn, address=PROG_MODE_ADDRESS, data=bytes([value]))
