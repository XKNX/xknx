"""Tests for the temporary routing through a coupler with the security extensions (not in spec)."""

from unittest.mock import AsyncMock

import pytest

from xknx.exceptions import ManagementConnectionError
from xknx.management.management import P2PConnection
from xknx.management.procedures import (
    CouplerSide,
    broadcast_routing_temp_read_conn,
    broadcast_routing_temp_write_conn,
    unicast_white_list_add_conn,
    unicast_white_list_check_conn,
    unicast_white_list_retrigger_conn,
    unicast_white_list_revoke_conn,
)
from xknx.telegram import IndividualAddress, Telegram
from xknx.telegram.apci import (
    APCI,
    FunctionPropertyExtCommand,
    FunctionPropertyExtStateRead,
    FunctionPropertyExtStateResponse,
    PropertyValueResponse,
    ReturnCode,
)

COUPLER = IndividualAddress("1.2.0")
TOOL = IndividualAddress("1.1.250")
DEVICE = IndividualAddress("1.2.5")


def _response(
    instance: int,
    property_id: int,
    data: bytes,
    return_code: ReturnCode | int = ReturnCode.E_SUCCESS,
) -> Telegram:
    return Telegram(
        source_address=COUPLER,
        destination_address=TOOL,
        payload=FunctionPropertyExtStateResponse(
            interface_object_type=6,
            object_instance=instance,
            property_id=property_id,
            return_code=return_code,
            data=data,
        ),
    )


def _conn(response: Telegram) -> tuple[P2PConnection, AsyncMock]:
    request = AsyncMock(return_value=response)
    conn = AsyncMock(spec=P2PConnection)
    conn.request = request
    return conn, request


def _sent(request: AsyncMock) -> APCI:
    payload: APCI = request.call_args.args[0]
    return payload


async def test_unicast_white_list_add() -> None:
    """A range of Partner Addresses is added for the User Address."""
    conn, request = _conn(_response(1, 83, b"\x00"))
    await unicast_white_list_add_conn(conn, TOOL, DEVICE, 3)
    assert _sent(request) == FunctionPropertyExtCommand(
        interface_object_type=6,
        object_instance=1,
        property_id=83,
        data=b"\x00\x00" + TOOL.to_knx() + DEVICE.to_knx() + b"\x00\x03",
    )
    with pytest.raises(ValueError, match="count"):
        await unicast_white_list_add_conn(conn, TOOL, DEVICE, 0x10000)


async def test_unicast_white_list_revoke_and_retrigger() -> None:
    """The list of the User Address is revoked, or its 60 s restarted."""
    conn, request = _conn(_response(1, 83, b"\x01"))
    await unicast_white_list_revoke_conn(conn, TOOL)
    assert _sent(request) == FunctionPropertyExtCommand(
        interface_object_type=6,
        object_instance=1,
        property_id=83,
        data=b"\x00\x01" + TOOL.to_knx(),
    )
    conn, request = _conn(_response(1, 83, b"\x02"))
    await unicast_white_list_retrigger_conn(conn, TOOL)
    assert _sent(request) == FunctionPropertyExtCommand(
        interface_object_type=6,
        object_instance=1,
        property_id=83,
        data=b"\x00\x02" + TOOL.to_knx(),
    )


@pytest.mark.parametrize("presence", [0, 1])
async def test_unicast_white_list_check(presence: int) -> None:
    """The check reads whether the list has all Partner Addresses of the range."""
    conn, request = _conn(_response(1, 83, bytes((0, presence))))
    assert await unicast_white_list_check_conn(conn, TOOL, DEVICE) is bool(presence)
    assert _sent(request) == FunctionPropertyExtStateRead(
        interface_object_type=6,
        object_instance=1,
        property_id=83,
        data=b"\x00\x00" + TOOL.to_knx() + DEVICE.to_knx() + b"\x00\x01",
    )
    with pytest.raises(ValueError, match="count"):
        await unicast_white_list_check_conn(conn, TOOL, DEVICE, -1)


async def test_unicast_white_list_check_without_result() -> None:
    """A check answered without its result is an error."""
    conn, _ = _conn(_response(1, 83, b"\x00"))
    with pytest.raises(ManagementConnectionError, match="without a result"):
        await unicast_white_list_check_conn(conn, TOOL, DEVICE)


@pytest.mark.parametrize(
    ("side", "enabled", "system_broadcast", "data"),
    [
        (CouplerSide.PRIMARY, True, False, b"\x00\x00\x01"),
        (CouplerSide.SECONDARY, False, False, b"\x00\x00\x00"),
        (CouplerSide.SECONDARY, True, True, b"\x00\x01\x01"),
    ],
)
async def test_broadcast_routing_temp_write(
    side: CouplerSide, enabled: bool, system_broadcast: bool, data: bytes
) -> None:
    """The broadcast or system broadcast routing mode of a side is set."""
    conn, request = _conn(_response(side, 84, data[1:2]))
    await broadcast_routing_temp_write_conn(
        conn, side, enabled, system_broadcast=system_broadcast
    )
    assert _sent(request) == FunctionPropertyExtCommand(
        interface_object_type=6, object_instance=side, property_id=84, data=data
    )


@pytest.mark.parametrize(("mode", "enabled"), [(0, False), (1, True)])
async def test_broadcast_routing_temp_read(mode: int, enabled: bool) -> None:
    """The routing mode of a side is read."""
    conn, request = _conn(_response(2, 84, bytes((1, mode))))
    assert (
        await broadcast_routing_temp_read_conn(
            conn, CouplerSide.SECONDARY, system_broadcast=True
        )
        is enabled
    )
    assert _sent(request) == FunctionPropertyExtStateRead(
        interface_object_type=6, object_instance=2, property_id=84, data=b"\x00\x01"
    )
    conn, _ = _conn(_response(2, 84, b"\x01"))
    with pytest.raises(ManagementConnectionError, match="without the routing mode"):
        await broadcast_routing_temp_read_conn(conn, CouplerSide.SECONDARY)


@pytest.mark.parametrize(
    ("return_code", "name"),
    [(ReturnCode.E_COMMAND_INVALID, "E_COMMAND_INVALID"), (0x30, "0x30")],
)
async def test_a_refusal(return_code: ReturnCode | int, name: str) -> None:
    """A return code other than E_SUCCESS raises, named."""
    conn, _ = _conn(_response(1, 84, b"\x01", return_code))
    with pytest.raises(
        ManagementConnectionError,
        match=rf"coupler 1\.2\.0 refused property 84 service 01: {name}",
    ):
        await broadcast_routing_temp_write_conn(
            conn, CouplerSide.PRIMARY, True, system_broadcast=True
        )


async def test_an_answer_of_something_else() -> None:
    """An answer that is not the function property's response is an error."""
    conn, _ = _conn(_response(2, 84, b"\x00"))
    with pytest.raises(ManagementConnectionError, match="response expected"):
        await broadcast_routing_temp_write_conn(conn, CouplerSide.PRIMARY, True)
    conn, _ = _conn(
        Telegram(
            source_address=COUPLER,
            destination_address=TOOL,
            payload=PropertyValueResponse(
                object_index=0, property_id=1, count=1, start_index=1, data=b"\x00"
            ),
        )
    )
    with pytest.raises(ManagementConnectionError, match="response expected"):
        await unicast_white_list_revoke_conn(conn, TOOL)
