"""Tests for prog_mode_property_switch_conn and prog_mode_switch (not in spec)."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError, PropertyVerificationError
from xknx.management.procedures.device.prog_mode_switch import (
    _PROG_MODE_MEMORY_MASKS,
    _PROG_MODE_PROPERTY_MASKS,
    prog_mode_property_switch_conn,
    prog_mode_switch,
)
from xknx.profile.const import ResourceDevicePropertyId
from xknx.telegram import IndividualAddress, Telegram, apci, tpci

from .test_dmp_prog_mode_switch_r_co import (
    _descriptor,
    _descriptor_read,
    _process,
    _switch_memory,
    _wait_for_calls,
)


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _property_response(value: bytes) -> apci.PropertyValueResponse:
    """Return the A_PropertyValue_Response echoing PID_PROGMODE."""
    return apci.PropertyValueResponse(
        object_index=0,
        property_id=ResourceDevicePropertyId.PID_PROGMODE,
        count=1,
        start_index=1,
        data=value,
    )


def _property_write(ia: IndividualAddress, value: bytes, seq: int) -> Telegram:
    """Return the A_PropertyValue_Write of PID_PROGMODE."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(seq),
        payload=apci.PropertyValueWrite(
            object_index=0,
            property_id=ResourceDevicePropertyId.PID_PROGMODE,
            count=1,
            start_index=1,
            data=value,
        ),
    )


@pytest.mark.parametrize("verify", [False, True])
@pytest.mark.parametrize("mode", [True, False])
async def test_prog_mode_property_switch_conn(
    xknx_setup: XKNX, mode: bool, verify: bool
) -> None:
    """Test PID_PROGMODE is written without reading it first."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    value = bytes([int(mode)])

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process(xknx, ia, ack_seq=0, payload=_property_response(value))

    responder = asyncio.create_task(respond())
    await prog_mode_property_switch_conn(conn, mode, verify=verify)
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(_property_write(ia, value, seq=0)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(0))),
    ]
    await conn.disconnect()


async def test_prog_mode_property_switch_conn_verify_rejected(
    xknx_setup: XKNX,
) -> None:
    """Test verify raises when the device's response keeps the old value."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process(xknx, ia, ack_seq=0, payload=_property_response(b"\x00"))

    responder = asyncio.create_task(respond())
    with pytest.raises(PropertyVerificationError):
        await prog_mode_property_switch_conn(conn, True, verify=True)
    await responder
    await conn.disconnect()


@pytest.mark.parametrize("mask_version", sorted(_PROG_MODE_MEMORY_MASKS))
async def test_prog_mode_switch_memory(xknx_setup: XKNX, mask_version: int) -> None:
    """Test prog_mode_switch switches curr_prog_mode at 60h of a memory mask."""
    await _switch_memory(
        xknx_setup, IndividualAddress("4.0.10"), prog_mode_switch, mask_version
    )


@pytest.mark.parametrize("mask_version", sorted(_PROG_MODE_PROPERTY_MASKS))
@pytest.mark.parametrize("mode", [True, False])
async def test_prog_mode_switch_property(
    xknx_setup: XKNX, mask_version: int, mode: bool
) -> None:
    """Test prog_mode_switch writes PID_PROGMODE of a property mask, not memory 60h."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    value = bytes([int(mode)])

    async def respond() -> None:
        await _wait_for_calls(xknx, 2)
        _process(xknx, ia, ack_seq=0, payload=_descriptor(mask_version))
        await _wait_for_calls(xknx, 4)
        _process(xknx, ia, ack_seq=1, payload=_property_response(value), response_seq=1)

    responder = asyncio.create_task(respond())
    await prog_mode_switch(xknx, ia, mode, verify=True)
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(Telegram(destination_address=ia, tpci=tpci.TConnect())),
        call(_descriptor_read(ia)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(0))),
        call(_property_write(ia, value, seq=1)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(1))),
        call(Telegram(destination_address=ia, tpci=tpci.TDisconnect())),
    ]


async def test_prog_mode_switch_unknown_mask(xknx_setup: XKNX) -> None:
    """Test a device of an unknown mask version is left untouched."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    async def respond() -> None:
        await _wait_for_calls(xknx, 2)
        _process(xknx, ia, ack_seq=0, payload=_descriptor(0x0BAD))

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError, match="0BADh"):
        await prog_mode_switch(xknx, ia, True)
    await responder

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(Telegram(destination_address=ia, tpci=tpci.TConnect())),
        call(_descriptor_read(ia)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(0))),
        call(Telegram(destination_address=ia, tpci=tpci.TDisconnect())),
    ]


def test_masks_are_either_memory_or_property() -> None:
    """Test no mask version is in both lists."""
    assert not _PROG_MODE_MEMORY_MASKS & _PROG_MODE_PROPERTY_MASKS
