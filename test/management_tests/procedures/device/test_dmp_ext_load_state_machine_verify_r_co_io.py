"""Tests for dmp_ext_load_state_machine_verify_r_co_io — KNX v02.01.02 - Management Procedures 03.05.02 - §3.32.4."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import VerificationError
from xknx.management.procedures.device.dmp_ext_load_state_machine_verify_r_co_io import (
    dmp_ext_load_state_machine_verify_r_co_io,
)
from xknx.management.procedures.device.load_state import LoadState
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


def _xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _ack(ia: IndividualAddress, xknx: XKNX, sequence: int) -> Telegram:
    """Build an incoming TAck for a given sequence number."""
    return Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(sequence),
    )


def _state_response(
    ia: IndividualAddress, xknx: XKNX, sequence: int, state: LoadState
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
            return_code=apci.ReturnCode.E_SUCCESS,
            data=bytes([state]),
        ),
    )


async def test_dmp_ext_load_state_machine_verify_r_co_io_matches() -> None:
    """Test the procedure returns None when the read state matches expected_state."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dmp_ext_load_state_machine_verify_r_co_io(
            conn,
            interface_object_type=343,
            object_instance=1,
            expected_state=LoadState.LOADED,
        )
    )
    await asyncio.sleep(0)

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(_state_response(ia, xknx, 0, LoadState.LOADED))

    result = await task
    assert result is None

    await conn.disconnect()


async def test_dmp_ext_load_state_machine_verify_r_co_io_mismatch() -> None:
    """Test the procedure raises VerificationError when the read state doesn't match."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(
        dmp_ext_load_state_machine_verify_r_co_io(
            conn,
            interface_object_type=343,
            object_instance=1,
            expected_state=LoadState.LOADED,
        )
    )
    await asyncio.sleep(0)

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(_state_response(ia, xknx, 0, LoadState.LOADING))

    with pytest.raises(VerificationError, match=r"expected LOADED, got LOADING"):
        await task

    await conn.disconnect()
