"""DM_GroupObjectLink_Read_RCl — KNX v02.01.02 - Management Procedures 03.05.02 - §3.37.2."""

from __future__ import annotations

from dataclasses import dataclass, field

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci
from xknx.telegram.address import GroupAddress

__all__ = ["GroupObjectLink", "dm_group_object_link_read_r_cl"]

# A_Link_Read/_Write's start_index is a 4 bit field (KNX v02.01.01 -
# Application Layer 03.03.07 - §3.4.6.1/.2).
_MAX_START_INDEX = 0xF


@dataclass(slots=True)
class GroupObjectLink:
    """The Group Addresses linked to a Group Object, and which one is the sending address."""

    sending_address: int
    """Index (1-15) of the sending Group Address within group_addresses, 0 if none."""

    group_addresses: list[GroupAddress] = field(default_factory=list)


async def dm_group_object_link_read_r_cl(
    conn: P2PConnection, group_object_number: int
) -> GroupObjectLink:
    """
    Read the Group Addresses linked to a Group Object.

    DM_GroupObjectLink_Read_RCl — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.37.2. Requires an established connection (DM_Connect must
    be executed first).

    Reads in chunks of up to 6 Group Addresses per ``A_Link_Read`` (KNX
    v02.01.01 - Application Layer 03.03.07 - §3.4.6.1), continuing at
    start_index 1, 7, 13, ... as long as a response carries a full 6, per
    the spec's own loop condition.

    A response with ``start_index=0`` and an empty ``group_address_list``
    (a "negative response") also ends the loop - but §3.37.1 uses this
    exact same response for two situations it does not itself distinguish:
    "the addressed Group Object does not exist" and "there are no (more)
    Group Addresses linked from this start_index". This procedure cannot
    tell those apart either and does not raise for it - a negative response
    on the very first request is returned as an empty ``GroupObjectLink``,
    not an error.

    The 4 bit ``start_index`` field caps how far this procedure can ever
    read: requests only ever use 1, 7 or 13. A Group Object with more than
    18 linked Group Addresses has ones this service structurally cannot
    reach - reading that far would need start_index=19, which
    ``apci.LinkRead`` cannot even encode. Raises rather than silently
    returning a truncated list, since a Configuration Procedure acting on
    an incomplete link list could misprogram the device.

    :param conn: Active P2P connection to the device
    :param group_object_number: Number of the Group Object to read
    :return: The Group Addresses linked to the Group Object, and the index
        of the sending Group Address within that list
    :raises ManagementConnectionError: If the Group Object has more than 18
        Group Addresses linked, which the 4 bit start_index field cannot
        address
    """
    start_index = 1
    sending_address = 0
    group_addresses: list[GroupAddress] = []

    while True:
        if start_index > _MAX_START_INDEX:
            raise ManagementConnectionError(
                f"group object {group_object_number}: more than "
                f"{len(group_addresses)} Group Addresses linked - the 4 bit "
                "start_index field of A_Link_Read cannot address further ones"
            )
        response = await conn.request(
            apci.LinkRead(
                group_object_number=group_object_number, start_index=start_index
            )
        )
        payload = response.payload
        if payload.start_index == 0 and not payload.group_address_list:
            break
        sending_address = payload.sending_address
        group_addresses.extend(payload.group_address_list)
        if len(payload.group_address_list) < 6:
            break
        start_index += 6

    return GroupObjectLink(
        sending_address=sending_address, group_addresses=group_addresses
    )
