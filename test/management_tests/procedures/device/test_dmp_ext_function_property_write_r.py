"""Tests for dmp_ext_function_property_write_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.30.2."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.management.procedures.device.dmp_ext_function_property_write_r import (
    dmp_ext_function_property_write_r,
    dmp_ext_function_property_write_r_conn,
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
    interface_object_type: int,
    object_instance: int,
    property_id: int,
    data: bytes,
) -> Telegram:
    """Build the outgoing FunctionPropertyExtCommand telegram for a given sequence number."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(sequence),
        payload=apci.FunctionPropertyExtCommand(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            data=data,
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
    interface_object_type: int,
    object_instance: int,
    property_id: int,
    return_code: apci.ReturnCode,
    data: bytes,
) -> Telegram:
    """Build an incoming FunctionPropertyExtStateResponse telegram."""
    return Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(sequence),
        payload=apci.FunctionPropertyExtStateResponse(
            interface_object_type=interface_object_type,
            object_instance=object_instance,
            property_id=property_id,
            return_code=return_code,
            data=data,
        ),
    )


async def test_dmp_ext_function_property_write_r_conn_success() -> None:
    """Test dmp_ext_function_property_write_r_conn sends the command and returns the response."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dmp_ext_function_property_write_r_conn(
            conn,
            interface_object_type=343,
            object_instance=1,
            property_id=52,
            command=b"\x01",
        )
    )
    await asyncio.sleep(0)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(
            _command_request(
                ia,
                0,
                interface_object_type=343,
                object_instance=1,
                property_id=52,
                data=b"\x01",
            )
        )
    ]

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _state_response(
            ia,
            xknx,
            0,
            interface_object_type=343,
            object_instance=1,
            property_id=52,
            return_code=apci.ReturnCode.E_SUCCESS,
            data=b"\x42",
        )
    )

    response = await task
    assert response == apci.FunctionPropertyExtStateResponse(
        interface_object_type=343,
        object_instance=1,
        property_id=52,
        return_code=apci.ReturnCode.E_SUCCESS,
        data=b"\x42",
    )

    await conn.disconnect()


async def test_dmp_ext_function_property_write_r_conn_error_return_code_not_raised() -> (
    None
):
    """
    Test dmp_ext_function_property_write_r_conn does not raise on an error return code.

    Per the spec's own "Exception handling" clause, the meaning of
    return_code is Function Property specific and its handling depends on
    the Configuration Procedure using this one - so it is returned, not
    raised, same as the base (non-extended) procedure.
    """
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dmp_ext_function_property_write_r_conn(
            conn,
            interface_object_type=343,
            object_instance=1,
            property_id=52,
            command=b"\x01",
        )
    )
    await asyncio.sleep(0)

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _state_response(
            ia,
            xknx,
            0,
            interface_object_type=343,
            object_instance=1,
            property_id=52,
            return_code=apci.ReturnCode.E_COMMAND_INVALID,
            data=b"",
        )
    )

    response = await task
    assert response.return_code == apci.ReturnCode.E_COMMAND_INVALID
    assert response.data == b""

    await conn.disconnect()


async def test_dmp_ext_function_property_write_r_opens_and_closes_connection() -> None:
    """Test dmp_ext_function_property_write_r opens and closes its own connection."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    task = asyncio.create_task(
        dmp_ext_function_property_write_r(
            xknx,
            ia,
            interface_object_type=343,
            object_instance=2,
            property_id=60,
            command=b"\xff",
        )
    )
    await asyncio.sleep(0)

    connect = Telegram(destination_address=ia, tpci=tpci.TConnect())
    assert xknx.cemi_handler.send_telegram.call_args_list[0] == call(connect)

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _state_response(
            ia,
            xknx,
            0,
            interface_object_type=343,
            object_instance=2,
            property_id=60,
            return_code=apci.ReturnCode.E_SUCCESS,
            data=b"\x99",
        )
    )
    await asyncio.sleep(0)

    response = await task
    assert response == apci.FunctionPropertyExtStateResponse(
        interface_object_type=343,
        object_instance=2,
        property_id=60,
        return_code=apci.ReturnCode.E_SUCCESS,
        data=b"\x99",
    )

    disconnect = Telegram(destination_address=ia, tpci=tpci.TDisconnect())
    assert xknx.cemi_handler.send_telegram.call_args_list[-1] == call(disconnect)


async def test_dmp_ext_function_property_write_r_conn_command_too_long() -> None:
    """Test dmp_ext_function_property_write_r_conn rejects a command that doesn't fit max_apdu_length."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    with pytest.raises(ValueError, match=r"does not fit max_apdu_length 15"):
        await dmp_ext_function_property_write_r_conn(
            conn,
            interface_object_type=343,
            object_instance=1,
            property_id=52,
            command=b"\x00" * 10,
        )

    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dmp_ext_function_property_write_r_conn_max_apdu_length_not_positive() -> (
    None
):
    """Test dmp_ext_function_property_write_r_conn raises ValueError for max_apdu_length <= 0."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    with pytest.raises(ValueError, match=r"max_apdu_length must be positive, got 0"):
        await dmp_ext_function_property_write_r_conn(
            conn,
            interface_object_type=343,
            object_instance=1,
            property_id=52,
            command=b"",
            max_apdu_length=0,
        )

    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()
