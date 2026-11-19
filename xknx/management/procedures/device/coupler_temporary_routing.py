"""
Temporary routing through a coupler with the security extensions.

Not in spec: KNX AN192 v06 - Coupler security extensions - §2.3.1.3 and §2.3.1.4 define the
Function Properties PID_PTP_ROUTING_TEMP and PID_BC_ROUTING_TEMP of the Router Object, but no
management procedure for them. A coupler used as Security Proxy does not route point-to-point
messages onto a side whose PID_PTP_CONFIG is BLOCK, nor broadcast and system broadcast messages
onto a side whose PID_BC_CONFIG is BLOCK (§2.2.2.5, §2.2.2.6). These functions let a tool through
for a while:

  - A Temporary Unicast White List passes the point-to-point messages between its User Address
    (typically the tool's individual address) and its Partner Addresses (§2.3.1.3). It is kept
    in the Router Object of the Primary Side and ends 60 s after it was added or retriggered.
  - The temporary broadcast and system broadcast routing modes pass broadcast and system
    broadcast messages onto the side of their Router Object (§2.3.1.4); both end 60 s after
    either was enabled. The system broadcast routing mode is not supported for a Router Object
    representing a TP1 Segment (§2.7.2.1); there the broadcast routing mode covers both.

They use the extended Function Property services, which address the Router Object by its type
and instance (KNX v02.01.01 - Application Layer 03.03.07 - §3.4.8): instance 1 for the Primary
Side, 2 for the Secondary Side (KNX AN192 v06 - Coupler security extensions - §2.7.2).
"""

from __future__ import annotations

from enum import IntEnum

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.profile.const import ResourceObjectType, ResourceRouterPropertyId
from xknx.telegram.address import IndividualAddress, IndividualAddressableType
from xknx.telegram.apci import (
    FunctionPropertyExtCommand,
    FunctionPropertyExtStateRead,
    FunctionPropertyExtStateResponse,
    ReturnCode,
)

__all__ = [
    "CouplerSide",
    "broadcast_routing_temp_read_conn",
    "broadcast_routing_temp_write_conn",
    "unicast_white_list_add_conn",
    "unicast_white_list_check_conn",
    "unicast_white_list_retrigger_conn",
    "unicast_white_list_revoke_conn",
]

# KNX AN192 v06 - Coupler security extensions - §2.3.1.3.5 and §2.3.1.3.6
_ADD = 0x00
_REVOKE = 0x01
_RETRIGGER = 0x02
_CHECK = 0x00
# KNX AN192 v06 - Coupler security extensions - §2.3.1.4.4 and §2.3.1.4.5
_BROADCAST = 0x00
_SYSTEM_BROADCAST = 0x01


class CouplerSide(IntEnum):
    """The side of a coupler, as the instance of its Router Object."""

    PRIMARY = 1
    SECONDARY = 2


def _address(address: IndividualAddressableType) -> bytes:
    return IndividualAddress(address).to_knx()


async def _function_property(
    conn: P2PConnection,
    request: FunctionPropertyExtCommand | FunctionPropertyExtStateRead,
) -> bytes:
    """Send ``request`` and return the data of its response after the ServiceID."""
    response = await conn.request(request)
    payload = response.payload
    if (
        not isinstance(payload, FunctionPropertyExtStateResponse)
        or payload.interface_object_type != request.interface_object_type
        or payload.object_instance != request.object_instance
        or payload.property_id != request.property_id
    ):
        raise ManagementConnectionError(
            f"Function property response expected, received {payload}"
        )
    if payload.return_code != ReturnCode.E_SUCCESS:
        code = payload.return_code
        name = code.name if isinstance(code, ReturnCode) else f"{code:#04x}"
        raise ManagementConnectionError(
            f"The coupler {response.source_address} refused property "
            f"{request.property_id} service {request.data[1:2].hex()}: {name}"
        )
    return payload.data[1:]


async def _command(
    conn: P2PConnection,
    property_id: int,
    side: CouplerSide,
    data: bytes,
) -> bytes:
    return await _function_property(
        conn,
        FunctionPropertyExtCommand(
            interface_object_type=ResourceObjectType.OBJECT_ROUTER.value,
            object_instance=side,
            property_id=property_id,
            data=data,
        ),
    )


async def _state_read(
    conn: P2PConnection,
    property_id: int,
    side: CouplerSide,
    data: bytes,
) -> bytes:
    return await _function_property(
        conn,
        FunctionPropertyExtStateRead(
            interface_object_type=ResourceObjectType.OBJECT_ROUTER.value,
            object_instance=side,
            property_id=property_id,
            data=data,
        ),
    )


async def unicast_white_list_add_conn(
    conn: P2PConnection,
    user_address: IndividualAddressableType,
    start_address: IndividualAddressableType,
    count: int = 1,
) -> None:
    """
    Add Partner Addresses to the Temporary Unicast White List of a User Address.

    Not in spec: WriteServiceID 00h "Add to Temporary Unicast White List" of PID_PTP_ROUTING_TEMP
    (KNX AN192 v06 - Coupler security extensions - §2.3.1.3.5.1). The point-to-point messages
    between ``user_address`` and the ``count`` individual addresses from ``start_address`` on
    pass the coupler for 60 s; adding more for the same User Address extends its list and
    restarts that time. ``count`` 0 adds nothing. Requires an established connection to the
    coupler.

    :param conn: Active P2P connection to the coupler
    :param user_address: the address that uses the list, typically the tool's own
    :param start_address: the first Partner Address
    :param count: how many Partner Addresses, from ``start_address`` on
    :raises ManagementConnectionError: If the coupler refuses it, e.g. without resources for
        another list (E_COMMAND_IMPOSSIBLE) or for its own address (E_DATA_VOID)
    """
    if not 0 <= count <= 0xFFFF:
        raise ValueError(f"count {count} is not 0-65535")
    await _command(
        conn,
        ResourceRouterPropertyId.PID_PTP_ROUTING_TEMP,
        CouplerSide.PRIMARY,
        bytes((0, _ADD))
        + _address(user_address)
        + _address(start_address)
        + count.to_bytes(2, "big"),
    )


async def unicast_white_list_revoke_conn(
    conn: P2PConnection, user_address: IndividualAddressableType
) -> None:
    """
    Revoke the Temporary Unicast White List of a User Address.

    Not in spec: WriteServiceID 01h "Revoke Temporary Unicast White List" of
    PID_PTP_ROUTING_TEMP (KNX AN192 v06 - Coupler security extensions - §2.3.1.3.5.2). A User
    Address without a list is no error. Requires an established connection to the coupler.

    :param conn: Active P2P connection to the coupler
    :param user_address: the address whose list is revoked
    :raises ManagementConnectionError: If the coupler refuses it
    """
    await _command(
        conn,
        ResourceRouterPropertyId.PID_PTP_ROUTING_TEMP,
        CouplerSide.PRIMARY,
        bytes((0, _REVOKE)) + _address(user_address),
    )


async def unicast_white_list_retrigger_conn(
    conn: P2PConnection, user_address: IndividualAddressableType
) -> None:
    """
    Restart the 60 s of the Temporary Unicast White List of a User Address.

    Not in spec: WriteServiceID 02h "Retrigger Temporary Unicast White List" of
    PID_PTP_ROUTING_TEMP (KNX AN192 v06 - Coupler security extensions - §2.3.1.3.5.3). Requires
    an established connection to the coupler.

    :param conn: Active P2P connection to the coupler
    :param user_address: the address whose list is retriggered
    :raises ManagementConnectionError: If the coupler refuses it, e.g. when the User Address
        has no list (E_DATA_VOID)
    """
    await _command(
        conn,
        ResourceRouterPropertyId.PID_PTP_ROUTING_TEMP,
        CouplerSide.PRIMARY,
        bytes((0, _RETRIGGER)) + _address(user_address),
    )


async def unicast_white_list_check_conn(
    conn: P2PConnection,
    user_address: IndividualAddressableType,
    start_address: IndividualAddressableType,
    count: int = 1,
) -> bool:
    """
    Check whether the Temporary Unicast White List of a User Address has Partner Addresses.

    Not in spec: ReadServiceID 00h "Check Temporary Unicast White List" of
    PID_PTP_ROUTING_TEMP (KNX AN192 v06 - Coupler security extensions - §2.3.1.3.6.1). Requires
    an established connection to the coupler.

    :param conn: Active P2P connection to the coupler
    :param user_address: the address whose list is checked
    :param start_address: the first Partner Address looked for
    :param count: how many Partner Addresses, from ``start_address`` on
    :return: whether the list has all of them
    :raises ManagementConnectionError: If the coupler refuses it or answers without a result
    """
    if not 0 <= count <= 0xFFFF:
        raise ValueError(f"count {count} is not 0-65535")
    result = await _state_read(
        conn,
        ResourceRouterPropertyId.PID_PTP_ROUTING_TEMP,
        CouplerSide.PRIMARY,
        bytes((0, _CHECK))
        + _address(user_address)
        + _address(start_address)
        + count.to_bytes(2, "big"),
    )
    if not result:
        raise ManagementConnectionError(
            "The coupler answered the check without a result"
        )
    return bool(result[0])


async def broadcast_routing_temp_write_conn(
    conn: P2PConnection,
    side: CouplerSide,
    enabled: bool,
    *,
    system_broadcast: bool = False,
) -> None:
    """
    Enable or disable the temporary routing of broadcast or system broadcast messages.

    Not in spec: WriteServiceID 00h "Set BC Temporary Routing Mode" and 01h "Set SBC Temporary
    Routing Mode" of PID_BC_ROUTING_TEMP (KNX AN192 v06 - Coupler security extensions -
    §2.3.1.4.4). Enabled, the coupler routes broadcast (or, with ``system_broadcast``, system
    broadcast) messages onto ``side`` for 60 s, retriggered by every enable of either mode.
    Requires an established connection to the coupler.

    :param conn: Active P2P connection to the coupler
    :param side: the side the messages are routed onto
    :param enabled: True to enable, False to disable
    :param system_broadcast: the system broadcast routing mode instead of the broadcast one;
        not for a side that is a TP1 Segment (§2.7.2.1)
    :raises ManagementConnectionError: If the coupler refuses it, e.g. the system broadcast
        routing mode of a TP1 side (E_COMMAND_INVALID)
    """
    await _command(
        conn,
        ResourceRouterPropertyId.PID_BC_ROUTING_TEMP,
        side,
        bytes((0, _SYSTEM_BROADCAST if system_broadcast else _BROADCAST, int(enabled))),
    )


async def broadcast_routing_temp_read_conn(
    conn: P2PConnection,
    side: CouplerSide,
    *,
    system_broadcast: bool = False,
) -> bool:
    """
    Read whether the temporary routing of broadcast or system broadcast messages is enabled.

    Not in spec: ReadServiceID 00h "Get BC Temporary Routing Mode" and 01h "Get SBC Temporary
    Routing Mode" of PID_BC_ROUTING_TEMP (KNX AN192 v06 - Coupler security extensions -
    §2.3.1.4.5). Requires an established connection to the coupler.

    :param conn: Active P2P connection to the coupler
    :param side: the side the messages are routed onto
    :param system_broadcast: the system broadcast routing mode instead of the broadcast one
    :return: whether the mode is enabled
    :raises ManagementConnectionError: If the coupler refuses it or answers without the mode
    """
    result = await _state_read(
        conn,
        ResourceRouterPropertyId.PID_BC_ROUTING_TEMP,
        side,
        bytes((0, _SYSTEM_BROADCAST if system_broadcast else _BROADCAST)),
    )
    if not result:
        raise ManagementConnectionError("The coupler answered without the routing mode")
    return result[0] == 1
