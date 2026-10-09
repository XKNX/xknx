"""Tests for dm_function_property_write_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.30.1."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures import dm_function_property_write_r
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci

RESPONDER_TIMEOUT = 1


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


async def _wait_for_sent(xknx: XKNX, count: int) -> None:
    """Wait until `count` telegrams have been sent."""
    async with asyncio.timeout(RESPONDER_TIMEOUT):
        while xknx.cemi_handler.send_telegram.call_count < count:  # noqa: ASYNC110
            await asyncio.sleep(0)


async def test_dm_function_property_write_r_connection_oriented(
    xknx_setup: XKNX,
) -> None:
    """Test calling a Function Property over a point-to-point connection."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    response = apci.FunctionPropertyStateResponse(
        object_index=3, property_id=52, return_code=0, data=b"\x01\x02"
    )

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_sent(xknx, 1)
        for control in (tpci.TAck(0), tpci.TDataConnected(0)):
            xknx.management.process(
                Telegram(
                    source_address=ia,
                    destination_address=xknx.current_address,
                    direction=TelegramDirection.INCOMING,
                    tpci=control,
                    payload=response
                    if isinstance(control, tpci.TDataConnected)
                    else None,
                )
            )

    responder = asyncio.create_task(respond())
    result = await dm_function_property_write_r(
        conn, object_index=3, property_id=52, command=b"\x01"
    )
    await responder

    assert result == response
    assert xknx.cemi_handler.send_telegram.call_args_list[0] == call(
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(0),
            payload=apci.FunctionPropertyCommand(
                object_index=3, property_id=52, data=b"\x01"
            ),
        )
    )
    await conn.disconnect()


@pytest.mark.parametrize(
    "response",
    [
        apci.FunctionPropertyStateResponse(
            object_index=3, property_id=52, return_code=0xF2
        ),
        # not a Function Property - KNX v02.01.01 - Application Layer 03.03.07 - §3.4.7.3
        apci.FunctionPropertyStateResponse(
            object_index=3, property_id=52, return_code=None
        ),
    ],
)
async def test_dm_function_property_write_r_connectionless(
    xknx_setup: XKNX, response: apci.FunctionPropertyStateResponse
) -> None:
    """Test calling a Function Property connectionless; the return code is returned as is."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:

        async def respond() -> None:
            await _wait_for_sent(xknx, 1)
            xknx.management.process(
                Telegram(
                    source_address=ia,
                    destination_address=xknx.current_address,
                    direction=TelegramDirection.INCOMING,
                    tpci=tpci.TDataIndividual(),
                    payload=response,
                )
            )

        responder = asyncio.create_task(respond())
        result = await dm_function_property_write_r(
            connectionless, object_index=3, property_id=52
        )
        await responder

    assert result == response
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(
            Telegram(
                source_address=xknx.current_address,
                destination_address=ia,
                tpci=tpci.TDataIndividual(),
                payload=apci.FunctionPropertyCommand(object_index=3, property_id=52),
            )
        )
    ]


async def test_dm_function_property_write_r_wrong_property(xknx_setup: XKNX) -> None:
    """Test a response for another Function Property raises."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:

        async def respond() -> None:
            await _wait_for_sent(xknx, 1)
            xknx.management.process(
                Telegram(
                    source_address=ia,
                    destination_address=xknx.current_address,
                    direction=TelegramDirection.INCOMING,
                    tpci=tpci.TDataIndividual(),
                    payload=apci.FunctionPropertyStateResponse(
                        object_index=3, property_id=53, return_code=0
                    ),
                )
            )

        responder = asyncio.create_task(respond())
        with pytest.raises(ManagementConnectionError):
            await dm_function_property_write_r(
                connectionless, object_index=3, property_id=52
            )
        await responder


@pytest.mark.parametrize(
    ("object_index", "property_id"), [(-1, 0), (256, 0), (0, -1), (0, 256)]
)
async def test_dm_function_property_write_r_out_of_range(
    xknx_setup: XKNX, object_index: int, property_id: int
) -> None:
    """Test out of range arguments raise before anything is sent."""
    xknx = xknx_setup
    async with xknx.management.connectionless(IndividualAddress("4.0.10")) as conn:
        with pytest.raises(ValueError):
            await dm_function_property_write_r(conn, object_index, property_id)
    xknx.cemi_handler.send_telegram.assert_not_called()
