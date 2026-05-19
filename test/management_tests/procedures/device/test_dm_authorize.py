"""Tests for dmp_authorize_r_co - KNX 03.05.02 section 3.5 DM_Authorize."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.management.procedures.device.dm_authorize import (
    FREE_ACCESS_KEY,
    dmp_authorize2_r_co,
    dmp_authorize_r_co,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci


@pytest.fixture
def xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


async def test_dmp_authorize_r_co_with_key(xknx_setup: XKNX) -> None:
    """Test dmp_authorize_r_co sends AuthorizeRequest and returns level."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    test_key = 0x12345678

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dmp_authorize_r_co(conn, test_key))
    await asyncio.sleep(0)

    expected_request = Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.AuthorizeRequest(key=test_key),
    )
    assert xknx.cemi_handler.send_telegram.call_args_list == [call(expected_request)]

    ack = Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    response = Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.AuthorizeResponse(level=3),
    )
    xknx.management.process(ack)
    xknx.management.process(response)

    level = await task
    assert level == 3

    await conn.disconnect()


async def test_dmp_authorize_r_co_free_access(xknx_setup: XKNX) -> None:
    """Test dmp_authorize_r_co with free access key."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dmp_authorize_r_co(conn, FREE_ACCESS_KEY))
    await asyncio.sleep(0)

    expected_request = Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.AuthorizeRequest(key=FREE_ACCESS_KEY),
    )
    assert xknx.cemi_handler.send_telegram.call_args_list == [call(expected_request)]

    ack = Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    response = Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.AuthorizeResponse(level=15),
    )
    xknx.management.process(ack)
    xknx.management.process(response)

    level = await task
    assert level == 15

    await conn.disconnect()


async def test_dmp_authorize2_r_co_free_access_is_highest(xknx_setup: XKNX) -> None:
    """Test dmp_authorize2_r_co when free access gives level 0 (highest)."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    client_key = 0xABCDEF00

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dmp_authorize2_r_co(conn, client_key))
    await asyncio.sleep(0)

    ack = Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(0),
    )
    response = Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(0),
        payload=apci.AuthorizeResponse(level=0),
    )
    xknx.management.process(ack)
    xknx.management.process(response)

    level = await task
    assert level == 0

    await conn.disconnect()


async def test_dmp_authorize2_r_co_client_key_is_better(xknx_setup: XKNX) -> None:
    """Test dmp_authorize2_r_co when client key gives better access than free."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    client_key = 0xABCDEF00

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond_to_requests() -> None:
        while xknx.cemi_handler.send_telegram.call_count < 1:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack0 = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(0),
        )
        free_response = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(0),
            payload=apci.AuthorizeResponse(level=15),
        )
        xknx.management.process(ack0)
        xknx.management.process(free_response)

        while xknx.cemi_handler.send_telegram.call_count < 3:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack1 = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(1),
        )
        client_response = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(1),
            payload=apci.AuthorizeResponse(level=3),
        )
        xknx.management.process(ack1)
        xknx.management.process(client_response)

    responder = asyncio.create_task(respond_to_requests())
    level = await dmp_authorize2_r_co(conn, client_key)
    await responder

    assert level == 3

    await conn.disconnect()


async def test_dmp_authorize2_r_co_equal_levels(xknx_setup: XKNX) -> None:
    """Test dmp_authorize2_r_co when client key gives equal access to free — no re-auth."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    client_key = 0xABCDEF00

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond_to_requests() -> None:
        while xknx.cemi_handler.send_telegram.call_count < 1:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack0 = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(0),
        )
        free_response = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(0),
            payload=apci.AuthorizeResponse(level=5),
        )
        xknx.management.process(ack0)
        xknx.management.process(free_response)

        while xknx.cemi_handler.send_telegram.call_count < 3:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack1 = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(1),
        )
        client_response = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(1),
            payload=apci.AuthorizeResponse(level=5),
        )
        xknx.management.process(ack1)
        xknx.management.process(client_response)

    responder = asyncio.create_task(respond_to_requests())
    level = await dmp_authorize2_r_co(conn, client_key)
    await responder

    assert level == 5
    assert xknx.cemi_handler.send_telegram.call_count == 4  # connect + 2x authorize, no re-auth

    await conn.disconnect()


async def test_dmp_authorize2_r_co_free_access_is_better(xknx_setup: XKNX) -> None:
    """Test dmp_authorize2_r_co when free access is better than client key."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    client_key = 0xABCDEF00

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond_to_requests() -> None:
        while xknx.cemi_handler.send_telegram.call_count < 1:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack0 = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(0),
        )
        free_response = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(0),
            payload=apci.AuthorizeResponse(level=3),
        )
        xknx.management.process(ack0)
        xknx.management.process(free_response)

        while xknx.cemi_handler.send_telegram.call_count < 3:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack1 = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(1),
        )
        client_response = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(1),
            payload=apci.AuthorizeResponse(level=10),
        )
        xknx.management.process(ack1)
        xknx.management.process(client_response)

        while xknx.cemi_handler.send_telegram.call_count < 5:  # noqa: ASYNC110
            await asyncio.sleep(0)
        ack2 = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TAck(2),
        )
        reauth_response = Telegram(
            source_address=ia,
            destination_address=xknx.current_address,
            direction=TelegramDirection.INCOMING,
            tpci=tpci.TDataConnected(2),
            payload=apci.AuthorizeResponse(level=3),
        )
        xknx.management.process(ack2)
        xknx.management.process(reauth_response)

    responder = asyncio.create_task(respond_to_requests())
    level = await dmp_authorize2_r_co(conn, client_key)
    await responder

    assert level == 3

    await conn.disconnect()
