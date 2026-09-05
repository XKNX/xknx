"""DMP_ProgModeSwitch_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.13.2."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci

__all__ = ["dmp_prog_mode_switch_r_co"]

# KNX v01.10.01 - Resources 03.05.01 - §4.26.3.2: "The location of
# curr_prog_mode shall be the memory address 0060h."
_CURR_PROG_MODE_ADDRESS = 0x0060

_PROG_MODE_BIT = 0b0000_0001
_DONT_CARE_MASK = 0b0111_1110


async def dmp_prog_mode_switch_r_co(conn: P2PConnection, mode: bool) -> None:
    """
    Switch a device's Programming Mode on or off.

    DMP_ProgModeSwitch_RCo — KNX v02.01.02 - Management Procedures 03.05.02
    - §3.13.2. Requires an established connection (DM_Connect must be
    executed first). Realises Programming Mode as "Realisation Type 2" (KNX
    v01.10.01 - Resources 03.05.01 - §4.26.3): a read-modify-write of the
    single octet ``curr_prog_mode`` at memory address 0060h.

    That octet's bit 0 (``prog_mode``) is both set and read back as the
    Programming Mode state; bits 1-6 are don't-care and are echoed back
    unchanged. Bit 7 (``p_parity``) is recomputed from scratch as the true
    even parity of bits 0-6 - matching calimero-core's
    ``ManagementProceduresImpl.setProgrammingMode()`` - rather than toggled:
    §4.26.3.1 "Format and encoding" defines ``p_parity`` as "the parity bit
    of the complete octet", and recomputing it satisfies that definition
    unconditionally, including the one case a toggle cannot cover - the
    device's own current parity already being invalid (a state
    §4.26.3.4.1's footnote 96 calls abnormal: "[t]ypically the system is
    restarted if p_parity is invalid"). §4.26.3.4.1 also requires that
    "the variable p_parity shall be inverted, if the value of prog_mode is
    changed"; recomputing satisfies this too whenever the device's current
    parity was already valid, which is the only case that sentence
    actually describes - flipping exactly one bit always flips the parity
    that was already correct for the rest, so toggling and recomputing
    agree there and only diverge on an already-invalid octet, where
    recomputing repairs it instead of preserving the invalid value.

    :param conn: Active P2P connection to the device
    :param mode: True to switch Programming Mode on, False to switch it off
    :raises ManagementConnectionError: If the read response carries a
        different address than requested, or not exactly 1 octet
    """
    response = await conn.request(
        apci.MemoryRead(address=_CURR_PROG_MODE_ADDRESS, count=1)
    )
    if response.payload.address != _CURR_PROG_MODE_ADDRESS:
        raise ManagementConnectionError(
            f"Programming Mode switch failed: requested address "
            f"{_CURR_PROG_MODE_ADDRESS:#06x}, response echoed "
            f"{response.payload.address:#06x}"
        )
    if len(response.payload.data) != 1:
        raise ManagementConnectionError(
            f"Programming Mode switch failed: address "
            f"{_CURR_PROG_MODE_ADDRESS:#06x} returned "
            f"{len(response.payload.data)} octets, expected 1"
        )
    current = response.payload.data[0]

    new_prog_mode = _PROG_MODE_BIT if mode else 0
    bits_0_to_6 = (current & _DONT_CARE_MASK) | new_prog_mode
    parity = bits_0_to_6.bit_count() % 2
    new_byte = bits_0_to_6 | (parity << 7)

    await conn.send_data(
        apci.MemoryWrite(address=_CURR_PROG_MODE_ADDRESS, data=bytes([new_byte]))
    )
