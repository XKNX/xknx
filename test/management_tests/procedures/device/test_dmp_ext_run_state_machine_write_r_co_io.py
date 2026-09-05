"""Tests for dmp_ext_run_state_machine_write_r_co_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.34.4."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_ext_run_state_machine_write_r_co_io import (
    dmp_ext_run_state_machine_write_r_co_io,
)
from xknx.management.procedures.device.run_state import RunState, restart
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


def _xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _command_request(ia: IndividualAddress, sequence: int, data: bytes) -> Telegram:
    """Build the outgoing FunctionPropertyExtCommand telegram."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(sequence),
        payload=apci.FunctionPropertyExtCommand(
            interface_object_type=343, object_instance=1, property_id=6, data=data
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
            interface_object_type=343,
            object_instance=1,
            property_id=6,
            return_code=return_code,
            data=data,
        ),
    )


async def test_dmp_ext_run_state_machine_write_r_co_io_success() -> None:
    """Test the procedure sends the run event and returns the resulting state."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dmp_ext_run_state_machine_write_r_co_io(
            conn,
            interface_object_type=343,
            object_instance=1,
            event_data=restart(),
            max_apdu_length=16,
        )
    )
    await asyncio.sleep(0)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(_command_request(ia, 0, restart()))
    ]

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _state_response(
            ia,
            xknx,
            0,
            return_code=apci.ReturnCode.E_SUCCESS,
            data=bytes([RunState.STARTING]),
        )
    )

    state = await task
    assert state == RunState.STARTING

    await conn.disconnect()


async def test_dmp_ext_run_state_machine_write_r_co_io_default_max_apdu_length_never_fits() -> (
    None
):
    """
    Test the procedure raises ValueError with the default max_apdu_length.

    A 6 octet A_FunctionPropertyExtCommand header plus the fixed 10 octet
    run event is 16 octets - one past what an L_Data_Standard frame's 15
    octet default carries. A device answering only standard frames can
    therefore never accept this procedure at all.
    """
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    with pytest.raises(ValueError, match=r"does not fit max_apdu_length 15"):
        await dmp_ext_run_state_machine_write_r_co_io(
            conn,
            interface_object_type=343,
            object_instance=1,
            event_data=restart(),
        )

    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dmp_ext_run_state_machine_write_r_co_io_wrong_event_length() -> None:
    """Test the procedure raises ValueError for event_data that isn't 10 octets."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"event_data must be 10 octets, got 3"):
        await dmp_ext_run_state_machine_write_r_co_io(
            conn,
            interface_object_type=343,
            object_instance=1,
            event_data=b"\x01\x00\x00",
        )
    await conn.disconnect()


async def test_dmp_ext_run_state_machine_write_r_co_io_negative_return_code_raises() -> (
    None
):
    """Test the procedure raises ManagementConnectionError on a negative return code."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dmp_ext_run_state_machine_write_r_co_io(
            conn,
            interface_object_type=343,
            object_instance=1,
            event_data=restart(),
            max_apdu_length=16,
        )
    )
    await asyncio.sleep(0)

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _state_response(
            ia,
            xknx,
            0,
            return_code=apci.ReturnCode.E_COMMAND_IMPOSSIBLE,
            data=b"",
        )
    )

    with pytest.raises(ManagementConnectionError, match=r"E_COMMAND_IMPOSSIBLE"):
        await task

    await conn.disconnect()


async def test_dmp_ext_run_state_machine_write_r_co_io_unknown_state() -> None:
    """Test the procedure raises when the device reports an undefined state value."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dmp_ext_run_state_machine_write_r_co_io(
            conn,
            interface_object_type=343,
            object_instance=1,
            event_data=restart(),
            max_apdu_length=16,
        )
    )
    await asyncio.sleep(0)

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _state_response(
            ia,
            xknx,
            0,
            return_code=apci.ReturnCode.E_SUCCESS,
            data=bytes([0xFF]),
        )
    )

    with pytest.raises(ManagementConnectionError, match=r"unknown state 0xff"):
        await task

    await conn.disconnect()
