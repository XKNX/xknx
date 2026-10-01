"""Tests for dmp_ext_load_state_machine_write_r_co_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.31.5."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_ext_load_state_machine_write_r_co_io import (
    dmp_ext_load_state_machine_write_r_co_io,
)
from xknx.management.procedures.device.load_state import LoadState, start_loading
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
            interface_object_type=343, object_instance=1, property_id=5, data=data
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
    return_code: apci.ReturnCode | int,
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
            property_id=5,
            return_code=return_code,
            data=data,
        ),
    )


async def _write(
    return_code: apci.ReturnCode | int, data: bytes
) -> tuple[XKNX, IndividualAddress, asyncio.Task[LoadState]]:
    """Start the procedure and answer it with the given response."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dmp_ext_load_state_machine_write_r_co_io(
            conn,
            interface_object_type=343,
            object_instance=1,
            event_data=start_loading(),
            max_apdu_length=16,
        )
    )
    await asyncio.sleep(0)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(_command_request(ia, 0, start_loading()))
    ]
    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _state_response(ia, xknx, 0, return_code=return_code, data=data)
    )
    return xknx, ia, task


async def test_dmp_ext_load_state_machine_write_r_co_io_success() -> None:
    """Test the procedure sends the load event and returns the resulting state."""
    _, _, task = await _write(apci.ReturnCode.E_SUCCESS, bytes([LoadState.LOADING]))
    assert await task == LoadState.LOADING


async def test_dmp_ext_load_state_machine_write_r_co_io_generic_positive_return_code() -> (
    None
):
    """
    Test a generic positive return code (01h-1Fh) is accepted, not only E_SUCCESS.

    KNX v02.01.01 - Application Layer 03.03.07 - §3.4.8.4: a positive return
    code carries the state.
    """
    _, _, task = await _write(0x01, bytes([LoadState.LOADING]))
    assert await task == LoadState.LOADING


@pytest.mark.parametrize(
    ("return_code", "match"),
    [
        (apci.ReturnCode.E_COMMAND_IMPOSSIBLE, r"write failed: E_COMMAND_IMPOSSIBLE"),
        (0xA0, r"write failed: 0xa0"),
    ],
)
async def test_dmp_ext_load_state_machine_write_r_co_io_negative_return_code_raises(
    return_code: apci.ReturnCode | int, match: str
) -> None:
    """Test the procedure raises ManagementConnectionError on a negative return code."""
    _, _, task = await _write(return_code, b"")
    with pytest.raises(ManagementConnectionError, match=match):
        await task


async def test_dmp_ext_load_state_machine_write_r_co_io_unknown_state() -> None:
    """Test the procedure raises when the device reports an undefined state value."""
    _, _, task = await _write(apci.ReturnCode.E_SUCCESS, bytes([0xFF]))
    with pytest.raises(ManagementConnectionError, match=r"unknown state 0xff"):
        await task


async def test_dmp_ext_load_state_machine_write_r_co_io_max_apdu_length_too_small() -> (
    None
):
    """
    Test the procedure raises ValueError for a standard frame's max_apdu_length.

    The 6 octet A_FunctionPropertyExtCommand header plus the fixed 10 octet
    load event is 16 octets, one past what an L_Data_Standard frame carries.
    """
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    with pytest.raises(ValueError, match=r"does not fit max_apdu_length 15"):
        await dmp_ext_load_state_machine_write_r_co_io(
            conn,
            interface_object_type=343,
            object_instance=1,
            event_data=start_loading(),
            max_apdu_length=15,
        )

    xknx.cemi_handler.send_telegram.assert_not_called()
    await conn.disconnect()


async def test_dmp_ext_load_state_machine_write_r_co_io_wrong_event_length() -> None:
    """Test the procedure raises ValueError for event_data that isn't 10 octets."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    with pytest.raises(ValueError, match=r"event_data must be 10 octets, got 3"):
        await dmp_ext_load_state_machine_write_r_co_io(
            conn,
            interface_object_type=343,
            object_instance=1,
            event_data=b"\x01\x00\x00",
            max_apdu_length=16,
        )
    await conn.disconnect()
