"""Tests for dm_function_property_write_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.30.1."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.management.procedures.device.dm_function_property_write_r import (
    dm_function_property_write_r,
    dm_function_property_write_r_conn,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


def _xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _command_request(
    ia: IndividualAddress,
    sequence: int,
    object_index: int,
    property_id: int,
    data: bytes,
) -> Telegram:
    """Build the outgoing FunctionPropertyCommand telegram for a given sequence number."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(sequence),
        payload=apci.FunctionPropertyCommand(
            object_index=object_index, property_id=property_id, data=data
        ),
    )


def _ack(ia: IndividualAddress, xknx: XKNX, sequence: int) -> Telegram:
    """Build an incoming TAck for a given sequence number."""
    return Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(sequence),
    )


def _state_response(
    ia: IndividualAddress,
    xknx: XKNX,
    sequence: int,
    object_index: int,
    property_id: int,
    return_code: int,
    data: bytes,
) -> Telegram:
    """Build an incoming FunctionPropertyStateResponse telegram."""
    return Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(sequence),
        payload=apci.FunctionPropertyStateResponse(
            object_index=object_index,
            property_id=property_id,
            return_code=return_code,
            data=data,
        ),
    )


async def test_dm_function_property_write_r_conn_success() -> None:
    """Test dm_function_property_write_r_conn sends the command and returns the response."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dm_function_property_write_r_conn(
            conn, object_index=3, property_id=10, command=b"\x01"
        )
    )
    await asyncio.sleep(0)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(_command_request(ia, 0, object_index=3, property_id=10, data=b"\x01"))
    ]

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _state_response(
            ia, xknx, 0, object_index=3, property_id=10, return_code=0, data=b"\x42"
        )
    )

    response = await task
    assert response == apci.FunctionPropertyStateResponse(
        object_index=3, property_id=10, return_code=0, data=b"\x42"
    )

    await conn.disconnect()


async def test_dm_function_property_write_r_conn_nonzero_return_code_not_raised() -> (
    None
):
    """
    Test dm_function_property_write_r_conn does not raise on a nonzero return code.

    Per the spec's own "Error handling" clause, the meaning of return_code is
    Function Property specific and its handling depends on the Configuration
    Procedure using this one - so it is returned, not raised.
    """
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dm_function_property_write_r_conn(
            conn, object_index=3, property_id=10, command=b"\x01"
        )
    )
    await asyncio.sleep(0)

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _state_response(
            ia, xknx, 0, object_index=3, property_id=10, return_code=0x02, data=b""
        )
    )

    response = await task
    assert response.return_code == 0x02
    assert response.data == b""

    await conn.disconnect()


async def test_dm_function_property_write_r_opens_and_closes_connection() -> None:
    """Test dm_function_property_write_r opens and closes its own connection."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    task = asyncio.create_task(
        dm_function_property_write_r(
            xknx, ia, object_index=1, property_id=5, command=b"\xff"
        )
    )
    await asyncio.sleep(0)

    connect = Telegram(destination_address=ia, tpci=tpci.TConnect())
    assert xknx.cemi_handler.send_telegram.call_args_list[0] == call(connect)

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _state_response(
            ia, xknx, 0, object_index=1, property_id=5, return_code=0, data=b"\x99"
        )
    )
    await asyncio.sleep(0)

    response = await task
    assert response == apci.FunctionPropertyStateResponse(
        object_index=1, property_id=5, return_code=0, data=b"\x99"
    )

    disconnect = Telegram(destination_address=ia, tpci=tpci.TDisconnect())
    assert xknx.cemi_handler.send_telegram.call_args_list[-1] == call(disconnect)


async def test_dm_function_property_write_r_conn_command_too_long() -> None:
    """Test dm_function_property_write_r_conn rejects a command that doesn't fit max_apdu_length."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    with pytest.raises(ValueError, match=r"does not fit max_apdu_length 15"):
        await dm_function_property_write_r_conn(
            conn, object_index=3, property_id=10, command=b"\x00" * 13
        )

    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dm_function_property_write_r_conn_max_apdu_length_not_positive() -> None:
    """Test dm_function_property_write_r_conn raises ValueError for max_apdu_length <= 0."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    with pytest.raises(ValueError, match=r"max_apdu_length must be positive, got 0"):
        await dm_function_property_write_r_conn(
            conn, object_index=3, property_id=10, command=b"", max_apdu_length=0
        )

    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()
