"""Tests for dmp_ext_load_state_machine_read_r_co_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.33.4."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dmp_ext_load_state_machine_read_r_co_io import (
    dmp_ext_load_state_machine_read_r_co_io,
)
from xknx.management.procedures.device.load_state import LoadState
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


def _xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _read_request(ia: IndividualAddress, sequence: int) -> Telegram:
    """Build the outgoing FunctionPropertyExtStateRead telegram."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(sequence),
        payload=apci.FunctionPropertyExtStateRead(
            interface_object_type=343, object_instance=1, property_id=5
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
            property_id=5,
            return_code=return_code,
            data=data,
        ),
    )


async def test_dmp_ext_load_state_machine_read_r_co_io_success() -> None:
    """Test the procedure reads and decodes the current Load State."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dmp_ext_load_state_machine_read_r_co_io(
            conn, interface_object_type=343, object_instance=1
        )
    )
    await asyncio.sleep(0)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(_read_request(ia, 0))
    ]

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _state_response(
            ia,
            xknx,
            0,
            return_code=apci.ReturnCode.E_SUCCESS,
            data=bytes([LoadState.LOADED]),
        )
    )

    state = await task
    assert state == LoadState.LOADED

    await conn.disconnect()


async def test_dmp_ext_load_state_machine_read_r_co_io_negative_return_code_raises() -> (
    None
):
    """Test the procedure raises ManagementConnectionError on a negative return code."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dmp_ext_load_state_machine_read_r_co_io(
            conn, interface_object_type=343, object_instance=1
        )
    )
    await asyncio.sleep(0)

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _state_response(
            ia,
            xknx,
            0,
            return_code=apci.ReturnCode.E_ADDRESS_VOID,
            data=b"",
        )
    )

    with pytest.raises(ManagementConnectionError, match=r"E_ADDRESS_VOID"):
        await task

    await conn.disconnect()


async def test_dmp_ext_load_state_machine_read_r_co_io_unknown_state() -> None:
    """Test the procedure raises when the device reports an undefined state value."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dmp_ext_load_state_machine_read_r_co_io(
            conn, interface_object_type=343, object_instance=1
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
