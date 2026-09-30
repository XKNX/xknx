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
# A_Link_Response carries up to 6 Group Addresses; MP §3.37.2 increments
# start_index "by 6".
_CHUNK_SIZE = 6
_CHUNK_START_INDICES = (1, 7, 13)
# The most links reachable with start_index <= 15 in steps of 6.
_MAX_LINKS = 18


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
    03.05.02 - §3.37.2. "RCl" is the point-to-point connectionless mode
    (§1.2 Table 1) and the spec has no DM_Connect step. xknx has no
    connectionless point-to-point request API, so this runs over an open
    ``P2PConnection`` (T_Data_Connected, which KNX v02.01.01 - Application
    Layer 03.03.07 - Table 1 also allows for A_Link_*).

    Reads in chunks of up to 6 Group Addresses per ``A_Link_Read`` (KNX
    v02.01.01 - Application Layer 03.03.07 - §3.4.6.1), continuing at
    start_index 1, 7, 13 as long as a response carries a full 6, per the
    spec's own loop condition. Every response must echo the requested
    ``group_object_number``, and a positive one the requested
    ``start_index``.

    A response with ``start_index=0`` and an empty ``group_address_list``
    (a "negative response") also ends the loop. AL §3.4.6.1 uses it both
    when the Group Object doesn't exist and when "no Group Addresses are
    assigned to the Group Object from the request start index"; this
    procedure can't tell those apart and doesn't raise for it - a negative
    response on the very first request is returned as an empty
    ``GroupObjectLink``.

    ``start_index`` is a 4 bit field (1-15), so the spec's loop can't send a
    fourth request at 19. After a full chunk at 13, one more request at 15
    returns entries 15-20: at most 4 addresses there means the 18 already
    read are complete (entries 15-18 are repeats), more than 4 means there
    are more than 18, which this service can't reach - that raises rather
    than returning a truncated list, since a Configuration Procedure acting
    on an incomplete link list could misprogram the device.

    :param conn: Active P2P connection to the device
    :param group_object_number: Number of the Group Object to read
    :return: The Group Addresses linked to the Group Object, and the index
        of the sending Group Address within that list
    :raises ManagementConnectionError: If the Group Object has more than 18
        Group Addresses linked, or a response doesn't echo the request
    """
    sending_address = 0
    group_addresses: list[GroupAddress] = []

    for start_index in _CHUNK_START_INDICES:
        payload = await _link_read(conn, group_object_number, start_index)
        if payload is None:
            break
        sending_address = payload.sending_address
        group_addresses.extend(payload.group_address_list)
        if len(payload.group_address_list) < _CHUNK_SIZE:
            break
    else:
        # all three chunks were full - probe the last addressable index
        payload = await _link_read(conn, group_object_number, _MAX_START_INDEX)
        if payload is not None and len(payload.group_address_list) > (
            _MAX_LINKS - _MAX_START_INDEX + 1
        ):
            raise ManagementConnectionError(
                f"group object {group_object_number}: more than {_MAX_LINKS} "
                "Group Addresses linked - the 4 bit start_index field of "
                "A_Link_Read cannot address further ones"
            )

    return GroupObjectLink(
        sending_address=sending_address, group_addresses=group_addresses
    )


async def _link_read(
    conn: P2PConnection, group_object_number: int, start_index: int
) -> apci.LinkResponse | None:
    """Send one A_Link_Read; return the positive response, or None for a negative one."""
    response = await conn.request(
        apci.LinkRead(group_object_number=group_object_number, start_index=start_index)
    )
    payload = response.payload
    if payload.group_object_number != group_object_number:
        raise ManagementConnectionError(
            f"A_Link_Response for group object {payload.group_object_number} "
            f"does not match request (group object {group_object_number})"
        )
    if payload.start_index == 0 and not payload.group_address_list:
        return None
    if payload.start_index != start_index:
        raise ManagementConnectionError(
            f"group object {group_object_number}: A_Link_Response start_index "
            f"{payload.start_index} does not match request ({start_index})"
        )
    return payload
