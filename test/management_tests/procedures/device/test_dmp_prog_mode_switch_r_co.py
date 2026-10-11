"""Tests for dmp_prog_mode_switch_r_co — KNX v02.01.02 - Management Procedures 03.05.02 - §3.13.2."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures import PROG_MODE_ADDRESS, dmp_prog_mode_switch_r_co
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci

RESPONDER_TIMEOUT = 1


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _process(
    xknx: XKNX, ia: IndividualAddress, ack_seq: int, payload: apci.APCI | None = None
) -> None:
    """Inject the device's ACK (+ optional TDataConnected response) into the management layer."""
    xknx.management.process(
        Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(ack_seq),
        )
    )
    if payload is not None:
        xknx.management.process(
            Telegram(
                source_address=ia,
                destination_address=xknx.current_address,
                direction=TelegramDirection.INCOMING,
                tpci=tpci.TDataConnected(0),
                payload=payload,
            )
        )


async def _wait_for_calls(xknx: XKNX, count: int) -> None:
    """Wait until at least count telegrams have been sent."""
    async with asyncio.timeout(RESPONDER_TIMEOUT):
        while xknx.cemi_handler.send_telegram.call_count < count:  # noqa: ASYNC110
            await asyncio.sleep(0)


@pytest.mark.parametrize(
    ("current", "mode", "written"),
    [
        # prog_mode set, p_parity inverted, shared bits 1-6 kept
        (0x2E, True, 0xAF),
        (0xAF, False, 0x2E),
        (0x00, True, 0x81),
        (0x81, False, 0x00),
        # prog_mode already as requested: written back unchanged
        (0x81, True, 0x81),
        (0x2E, False, 0x2E),
    ],
)
async def test_dmp_prog_mode_switch_r_co(
    xknx_setup: XKNX, current: int, mode: bool, written: int
) -> None:
    """Test curr_prog_mode is read at 60h and written back with prog_mode and parity."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process(
            xknx,
            ia,
            ack_seq=0,
            payload=apci.MemoryResponse(
                address=PROG_MODE_ADDRESS, data=bytes([current])
            ),
        )
        await _wait_for_calls(xknx, 3)
        _process(xknx, ia, ack_seq=1)

    responder = asyncio.create_task(respond())
    await dmp_prog_mode_switch_r_co(conn, mode)
    await responder

    sent = [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list]
    assert sent[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.MemoryRead(address=PROG_MODE_ADDRESS, count=1),
    )
    assert sent[-1] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(1),
        payload=apci.MemoryWrite(address=PROG_MODE_ADDRESS, data=bytes([written])),
    )
    await conn.disconnect()


async def test_dmp_prog_mode_switch_r_co_no_data(xknx_setup: XKNX) -> None:
    """Test a read answered without data raises and writes nothing."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_calls(xknx, 1)
        _process(
            xknx,
            ia,
            ack_seq=0,
            payload=apci.MemoryResponse(address=PROG_MODE_ADDRESS, data=b""),
        )

    responder = asyncio.create_task(respond())
    with pytest.raises(ManagementConnectionError):
        await dmp_prog_mode_switch_r_co(conn, True)
    await responder

    assert not any(
        isinstance(c.args[0].payload, apci.MemoryWrite)
        for c in xknx.cemi_handler.send_telegram.call_args_list
    )
    await conn.disconnect()
