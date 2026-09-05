"""Tests for dm_identify_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.4.2."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.management.procedures.device.dm_identify_r import (
    IdentifiedDevice,
    dm_identify_r,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci

RESPONDER_TIMEOUT = 1


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _process_response(
    xknx: XKNX, ia: IndividualAddress, seq: int, payload: apci.APCI
) -> None:
    """Inject ACK + TDataConnected response into the management layer."""
    xknx.management.process(
        Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(seq),
        )
    )
    xknx.management.process(
        Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(seq),
            payload=payload,
        )
    )


async def _wait_for_request(xknx: XKNX, req_num: int) -> None:
    """Wait until the req_num-th request telegram has been sent (1-indexed)."""
    threshold = req_num * 2 - 1
    async with asyncio.timeout(RESPONDER_TIMEOUT):
        while xknx.cemi_handler.send_telegram.call_count < threshold:  # noqa: ASYNC110
            await asyncio.sleep(0)


async def test_dm_identify_r_non_legacy_device_skips_step_2(
    xknx_setup: XKNX,
) -> None:
    """Test dm_identify_r skips PID_MGT_DESCRIPTOR_01 when DD0 != 0300h."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx,
            ia,
            seq=0,
            payload=apci.DeviceDescriptorResponse(descriptor=0, value=0x07B0),
        )

    responder = asyncio.create_task(respond())
    result = await dm_identify_r(conn)
    await responder

    assert result == IdentifiedDevice(
        device_descriptor_type_0=0x07B0, management_model=None
    )
    assert xknx.cemi_handler.send_telegram.call_args_list[0].args[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.DeviceDescriptorRead(descriptor=0),
    )
    await conn.disconnect()


async def test_dm_identify_r_legacy_device_reads_management_model(
    xknx_setup: XKNX,
) -> None:
    """Test dm_identify_r reads PID_MGT_DESCRIPTOR_01 when DD0 == 0300h."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    management_model = bytes([0x01, 0x00, 0x00, 0x01]) + bytes(6)

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _process_response(
            xknx,
            ia,
            seq=0,
            payload=apci.DeviceDescriptorResponse(descriptor=0, value=0x0300),
        )
        await _wait_for_request(xknx, 2)
        _process_response(
            xknx,
            ia,
            seq=1,
            payload=apci.PropertyValueResponse(
                object_index=0,
                property_id=72,
                count=1,
                start_index=1,
                data=management_model,
            ),
        )

    responder = asyncio.create_task(respond())
    result = await dm_identify_r(conn)
    await responder

    assert result == IdentifiedDevice(
        device_descriptor_type_0=0x0300, management_model=management_model
    )
    assert xknx.cemi_handler.send_telegram.call_args_list[2].args[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(1),
        payload=apci.PropertyValueRead(
            object_index=0, property_id=72, count=1, start_index=1
        ),
    )
    await conn.disconnect()
