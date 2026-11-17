"""
Switching the Programming Mode wherever a device keeps it.

Not in spec: KNX v02.01.02 - Management Procedures 03.05.02 - §3.13 defines
DM_ProgMode_Switch only for memory 60h (see ``dmp_prog_mode_switch_r_co``).
These helpers cover devices that keep the Programming Mode in the Device
Object's ``PID_PROGMODE`` (KNX v01.10.01 - Resources 03.05.01 - §4.26.2 and
§4.3.5), and choose between the two by mask version.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceDevicePropertyId
from xknx.telegram.address import IndividualAddress, IndividualAddressableType

from .dm_connect_r_co import dmp_connect_r_co
from .dmp_interface_object_write_r import dmp_interface_object_write_r
from .dmp_prog_mode_switch_r_co import dmp_prog_mode_switch_r_co

if TYPE_CHECKING:
    from xknx import XKNX

__all__ = [
    "prog_mode_property_switch_conn",
    "prog_mode_switch",
]

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


async def prog_mode_property_switch_conn(
    conn: P2PConnection, mode: bool, verify: bool = False
) -> None:
    """
    Switch the Programming Mode of a device through the Device Object's PID_PROGMODE.

    Not in spec: KNX v02.01.02 - Management Procedures 03.05.02 - §3.13 defines
    DM_ProgMode_Switch only for memory 60h. This is the counterpart for devices
    realising the Programming Mode as "Programming Mode - Realisation Type 1"
    (KNX v01.10.01 - Resources 03.05.01 - §4.26.2). ``PID_PROGMODE`` is a
    PDT_BITSET8 with bit 0 as the Programming Mode and bits 1 to 7 reserved and
    0 (KNX v01.10.01 - Resources 03.05.01 - §4.3.5), so it is written without
    reading it first, also when the mode is already set. Requires an
    established connection.

    :param conn: Active P2P connection to the device
    :param mode: True to switch the Programming Mode on, False to switch it off
    :param verify: If True, the response has to echo the written value
    :raises ManagementConnectionError: If the device rejects the write
    :raises PropertyVerificationError: If verify is enabled and the response
        does not echo what was written
    """
    await dmp_interface_object_write_r(
        conn,
        0,
        ResourceDevicePropertyId.PID_PROGMODE,
        bytes([int(mode)]),
        verify=verify,
    )


async def prog_mode_switch(
    xknx: XKNX,
    individual_address: IndividualAddressableType,
    mode: bool,
    verify: bool = False,
) -> None:
    """
    Switch the Programming Mode of a device wherever its mask version keeps it.

    Not in spec: connects, executes DM_Connect and chooses by the mask version
    it reads (Device Descriptor Type 0) between memory 60h
    (:func:`dmp_prog_mode_switch_r_co`) and the Device Object's
    ``PID_PROGMODE`` (:func:`prog_mode_property_switch_conn`), then disconnects. A
    device of another mask version is left untouched.

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
        if mask_version in _PROG_MODE_MEMORY_MASKS:
            await dmp_prog_mode_switch_r_co(conn, mode, verify=verify)
        elif mask_version in _PROG_MODE_PROPERTY_MASKS:
            await prog_mode_property_switch_conn(conn, mode, verify=verify)
        else:
            raise ManagementConnectionError(
                f"Programming Mode location of mask version {mask_version:04X}h "
                "is not known"
            )
