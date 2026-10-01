"""DMP_ProgModeSwitch_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.13.2."""

from __future__ import annotations

from xknx.management.management import P2PConnection

from .dmp_mem_read_r_co import dmp_mem_read_r_co
from .dmp_mem_write_r_co import dmp_mem_write_r_co

__all__ = ["dmp_prog_mode_switch_r_co"]

# KNX v01.10.01 - Resources 03.05.01 - §4.26.3.2: "The location of
# curr_prog_mode shall be the memory address 0060h."
_CURR_PROG_MODE_ADDRESS = 0x0060

_PROG_MODE_BIT = 0b0000_0001
_DONT_CARE_MASK = 0b0111_1110


async def dmp_prog_mode_switch_r_co(
    conn: P2PConnection, mode: bool, *, verify: bool = False
) -> None:
    """
    Switch a device's Programming Mode on or off.

    DMP_ProgModeSwitch_RCo — KNX v02.01.02 - Management Procedures 03.05.02
    - §3.13.2. Requires an established connection (DM_Connect must be
    executed first). Realises Programming Mode as "Realisation Type 2" (KNX
    v01.10.01 - Resources 03.05.01 - §4.26.3): a read-modify-write of the
    single octet ``curr_prog_mode`` at memory address 0060h, via
    :func:`~.dmp_mem_read_r_co.dmp_mem_read_r_co` ("different or no data
    received ⇒ error") and
    :func:`~.dmp_mem_write_r_co.dmp_mem_write_r_co`.

    That octet's bit 0 (``prog_mode``) is both set and read back as the
    Programming Mode state; bits 1-6 are don't-care and are written back
    unchanged. Bit 7 (``p_parity``, "the parity bit of the complete octet",
    Resources §4.26.3.1) is recalculated as even parity over bits 0-6, as
    Management Procedures §3.13.2 requires ("The parity (bit 7) has to be
    calculated"). For a valid stored octet this equals Resources
    §4.26.3.4.1's "p_parity shall be inverted, if the value of prog_mode is
    changed"; an already-invalid parity bit is repaired.

    This always writes, even if the device is already in ``mode``; Resources
    §4.26.3.4.2/.3 wrap the switch in a configuration procedure that reads
    first and only switches if the mode differs.

    :param conn: Active P2P connection to the device
    :param mode: True to switch Programming Mode on, False to switch it off
    :param verify: Read the octet back after writing it and compare. The
        spec's sequence has no verify step, so it's off by default.
    :raises ManagementConnectionError: If the read response carries a
        different address than requested, or not exactly 1 octet
    :raises VerificationError: If ``verify`` is set and the read-back
        doesn't match
    """
    current = (await dmp_mem_read_r_co(conn, _CURR_PROG_MODE_ADDRESS, 1))[0]

    new_prog_mode = _PROG_MODE_BIT if mode else 0
    bits_0_to_6 = (current & _DONT_CARE_MASK) | new_prog_mode
    parity = bits_0_to_6.bit_count() % 2
    new_byte = bits_0_to_6 | (parity << 7)

    await dmp_mem_write_r_co(
        conn, _CURR_PROG_MODE_ADDRESS, bytes([new_byte]), verify=verify
    )
