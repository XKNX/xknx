"""DMP_ProgModeSwitch_RCo — KNX v02.01.02 - Management Procedures 03.05.02 - §3.13.2."""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceDevicePropertyId
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

from .dm_connect_r_co import dmp_connect_r_co
from .dmp_interface_object_write_r import dmp_interface_object_write_r
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

# Not in spec: where each mask version keeps its Programming Mode. KNX v01.10.01 - Resources
# 03.05.01 - §4.26.3 names only masks 0012h, 0020h, 0021h and 0701h for curr_prog_mode. Both
# lists are the "ProgrammingMode" resource of each mask version in the KNX master data
# (knx_master.xml MasterData Version 198, project schema 23). Schemas 14 and 20 list the same;
# schema 11 lacks 2705h, 27B0h and 2920h.
#
# Mask versions (Device Descriptor Type 0) whose Programming Mode is curr_prog_mode at 60h
# (Realisation Type 2). The master data lists the Device Object's PID_PROGMODE for 0912h and
# 091Ah as well; they are switched through memory 60h.
_PROG_MODE_MEMORY_MASKS = frozenset(
    {
        0x0010,
        0x0011,
        0x0012,
        0x0013,
        0x0020,
        0x0021,
        0x0025,
        0x0700,
        0x0701,
        0x0705,
        0x0900,
        0x0910,
        0x0911,
        0x0912,
        0x091A,
        0x1011,
        0x1012,
        0x1013,
        0x1900,
        0x5705,
    }
)
# Mask versions whose Programming Mode is only the Device Object's PID_PROGMODE (Realisation
# Type 1, KNX v01.10.01 - Resources 03.05.01 - §4.26.2 and §4.3.5).
_PROG_MODE_PROPERTY_MASKS = frozenset(
    {0x0300, 0x07B0, 0x17B0, 0x2705, 0x27B0, 0x2920, 0x57B0}
)


async def dmp_prog_mode_switch_r_co(
    conn: P2PConnection, mode: bool, verify: bool = False
) -> None:
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

    :func:`dm_prog_mode_switch` picks the right one by the device's mask
    version (not in spec).

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

    KNX v02.01.02 - Management Procedures 03.05.02 - §3.13 defines
    DM_ProgMode_Switch only for memory 60h (RCo and LEmi1). Not in spec: this
    function reads the device's mask version (Device Descriptor Type 0) when
    connecting and decides by it where the Programming Mode is: memory 60h
    (:func:`dmp_prog_mode_switch_r_co`) or the Device Object's
    ``PID_PROGMODE`` (KNX v01.10.01 - Resources 03.05.01 - §4.3.5), as the KNX
    master data lists it per mask version. A device of another mask version is
    left untouched.

    The memory path writes nothing when ``prog_mode`` already equals ``mode``;
    the property path always writes, since all other bits of ``PID_PROGMODE``
    are reserved and 0.

    :param xknx: the XKNX object
    :param individual_address: address of the device
    :param mode: True to switch the Programming Mode on, False to switch it off
    :param verify: If True, confirm the written value: memory 60h is read back,
        the property's response has to echo it
    :raises ManagementConnectionError: If the Programming Mode location of the
        device's mask version is not known, or the device answers with no data,
        a different address or an error
    :raises VerificationError: If verify is enabled and the read-back does not
        match what was written (memory 60h)
    :raises PropertyVerificationError: If verify is enabled and the response
        does not echo what was written (PID_PROGMODE)
    """
    async with xknx.management.connection(
        IndividualAddress(individual_address)
    ) as conn:
        mask_version = await dmp_connect_r_co(conn)
        # Not in spec: the location is chosen by the mask version.
        if mask_version in _PROG_MODE_MEMORY_MASKS:
            await dmp_prog_mode_switch_r_co(conn, mode, verify=verify)
        elif mask_version in _PROG_MODE_PROPERTY_MASKS:
            # Not in spec: Realisation Type 1 through PID_PROGMODE. PDT_BITSET8: bit 0 is the
            # Programming Mode, bits 1-7 are reserved and 0, so it is written without reading
            # it first, also when the mode is already set.
            await dmp_interface_object_write_r(
                conn,
                0,
                ResourceDevicePropertyId.PID_PROGMODE,
                bytes([int(mode)]),
                verify=verify,
            )
        else:
            raise ManagementConnectionError(
                f"Programming Mode location of mask version {mask_version:04X}h "
                "is not known"
            )
