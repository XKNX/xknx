"""DM_GroupObjectLink_Write_RCl — KNX v02.01.02 - Management Procedures 03.05.02 - §3.37.3."""

from __future__ import annotations

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.telegram import apci
from xknx.telegram.address import GroupAddress

from .dm_group_object_link_read_r_cl import GroupObjectLink

__all__ = ["dm_group_object_link_write_r_cl"]


async def dm_group_object_link_write_r_cl(
    conn: P2PConnection,
    group_object_number: int,
    group_address: GroupAddress,
    *,
    delete: bool = False,
    sending: bool = False,
) -> GroupObjectLink:
    """
    Add or remove a Group Address link on a Group Object.

    DM_GroupObjectLink_Write_RCl — KNX v02.01.02 - Management Procedures
    03.05.02 - §3.37.3. Requires an established connection (DM_Connect must
    be executed first). The Management Client is responsible for having
    already checked ``group_address`` is free before adding it (§3.37.1) -
    this procedure does not do that itself.

    The response echoes the resulting link list starting at index 1, up to
    the first 6 Group Addresses only (§3.37.3 note (1)) - not necessarily
    including the address just added, if the Group Object already had 6 or
    more linked. Call
    :func:`~.dm_group_object_link_read_r_cl.dm_group_object_link_read_r_cl`
    afterwards for the complete, current list.

    :param conn: Active P2P connection to the device
    :param group_object_number: Number of the Group Object to modify
    :param group_address: The Group Address to add or remove
    :param delete: If True, remove group_address instead of adding it
    :param sending: If the address is added (delete=False), whether it
        becomes the Group Object's sending address. Ignored when deleting.
    :return: The (possibly partial, see above) resulting list of linked
        Group Addresses and the sending address index
    :raises ManagementConnectionError: If the device responds with a
        negative A_Link_Response (§3.37.1: table full, non-existing Group
        Object, invalid reserved bits, ...)
    """
    response = await conn.request(
        apci.LinkWrite(
            group_object_number=group_object_number,
            group_address=group_address,
            delete=delete,
            sending=sending,
        )
    )
    payload = response.payload
    if payload.start_index == 0 and not payload.group_address_list:
        raise ManagementConnectionError(
            f"group object {group_object_number}: negative A_Link_Response "
            f"writing group address {group_address}"
        )
    return GroupObjectLink(
        sending_address=payload.sending_address,
        group_addresses=payload.group_address_list,
    )
