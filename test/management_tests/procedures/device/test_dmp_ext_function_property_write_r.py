"""Tests for dmp_ext_function_property_write_r — KNX v02.01.02 - Management Procedures 03.05.02 - §3.30.2."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures import (
    dmp_ext_function_property_write_r,
    dmp_ext_function_property_write_r_cl,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci

RESPONDER_TIMEOUT = 1


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _response(
    interface_object_type: int = 0x0B, object_instance: int = 1, property_id: int = 7
) -> apci.FunctionPropertyExtStateResponse:
    return apci.FunctionPropertyExtStateResponse(
        interface_object_type=interface_object_type,
        object_instance=object_instance,
        property_id=property_id,
        return_code=0x00,
        data=b"\x2a",
    )


async def _respond(xknx: XKNX, ia: IndividualAddress, payload: apci.APCI) -> None:
    """Answer the first request connectionless."""
    async with asyncio.timeout(RESPONDER_TIMEOUT):
        while not xknx.cemi_handler.send_telegram.call_count:  # noqa: ASYNC110
            await asyncio.sleep(0)
    xknx.management.process(
        Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataIndividual(),
            payload=payload,
        )
    )


async def test_dmp_ext_function_property_write_r(xknx_setup: XKNX) -> None:
    """Test calling a Function Property addressed by object type and instance."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        responder = asyncio.create_task(_respond(xknx, ia, _response()))
        result = await dmp_ext_function_property_write_r_cl(
            connectionless,
            interface_object_type=0x0B,
            object_instance=1,
            property_id=7,
            command=b"\x05",
        )
        await responder

    assert result == _response()
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(
            Telegram(
                source_address=xknx.current_address,
                destination_address=ia,
                tpci=tpci.TDataIndividual(),
                payload=apci.FunctionPropertyExtCommand(
                    interface_object_type=0x0B,
                    object_instance=1,
                    property_id=7,
                    data=b"\x05",
                ),
            )
        )
    ]


async def test_dmp_ext_function_property_write_r_connection_oriented(
    xknx_setup: XKNX,
) -> None:
    """Test calling a Function Property over a point-to-point connection."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        async with asyncio.timeout(RESPONDER_TIMEOUT):
            while not xknx.cemi_handler.send_telegram.call_count:  # noqa: ASYNC110
                await asyncio.sleep(0)
        for control in (tpci.TAck(0), tpci.TDataConnected(0)):
            xknx.management.process(
                Telegram(
                    source_address=ia,
                    destination_address=xknx.current_address,
                    direction=TelegramDirection.INCOMING,
                    tpci=control,
                    payload=_response()
                    if isinstance(control, tpci.TDataConnected)
                    else None,
                )
            )

    responder = asyncio.create_task(respond())
    result = await dmp_ext_function_property_write_r(
        conn,
        interface_object_type=0x0B,
        object_instance=1,
        property_id=7,
        command=b"\x05",
    )
    await responder

    assert result == _response()
    assert xknx.cemi_handler.send_telegram.call_args_list[0] == call(
        Telegram(
            destination_address=ia,
            tpci=tpci.TDataConnected(0),
            payload=apci.FunctionPropertyExtCommand(
                interface_object_type=0x0B,
                object_instance=1,
                property_id=7,
                data=b"\x05",
            ),
        )
    )
    await conn.disconnect()


async def test_dmp_ext_function_property_write_r_specific_return_code(
    xknx_setup: XKNX,
) -> None:
    """Test a function specific return code is returned as is."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    # return_code 21h, no data
    response = apci.APCI.from_knx(bytes.fromhex("01d6000b00100721"))

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        responder = asyncio.create_task(_respond(xknx, ia, response))
        result = await dmp_ext_function_property_write_r_cl(
            connectionless,
            interface_object_type=0x0B,
            object_instance=1,
            property_id=7,
        )
        await responder

    assert result.return_code == 0x21
    assert result.data == b""


@pytest.mark.parametrize(
    ("interface_object_type", "object_instance", "property_id"),
    [(0x0B, 1, 8), (0x0C, 1, 7), (0x0B, 2, 7)],
)
async def test_dmp_ext_function_property_write_r_wrong_property(
    xknx_setup: XKNX,
    interface_object_type: int,
    object_instance: int,
    property_id: int,
) -> None:
    """Test a response for another Interface Object or Property raises."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    response = _response(interface_object_type, object_instance, property_id)

    async with xknx.management.connectionless(ia, rate_limit=0) as connectionless:
        responder = asyncio.create_task(_respond(xknx, ia, response))
        with pytest.raises(ManagementConnectionError):
            await dmp_ext_function_property_write_r_cl(
                connectionless,
                interface_object_type=0x0B,
                object_instance=1,
                property_id=7,
            )
        await responder


@pytest.mark.parametrize(
    ("interface_object_type", "object_instance", "property_id"),
    [(-1, 1, 7), (0x10000, 1, 7), (0x0B, -1, 7), (0x0B, 0x1000, 7), (0x0B, 1, 0x1000)],
)
async def test_dmp_ext_function_property_write_r_out_of_range(
    xknx_setup: XKNX,
    interface_object_type: int,
    object_instance: int,
    property_id: int,
) -> None:
    """Test out of range arguments raise before anything is sent."""
    xknx = xknx_setup
    async with xknx.management.connectionless(IndividualAddress("4.0.10")) as conn:
        with pytest.raises(ValueError):
            await dmp_ext_function_property_write_r_cl(
                conn, interface_object_type, object_instance, property_id
            )
    xknx.cemi_handler.send_telegram.assert_not_called()
