"""Tests for dmp_authorize_r_co - KNX v02.01.02 - Management Procedures 03.05.02 - §3.5 DM_Authorize."""

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
from xknx.util import asyncio_timeout

RESPONDER_TIMEOUT = 1


@pytest.fixture
def xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _authorize_request(ia: IndividualAddress, sequence: int, key: int) -> Telegram:
    """Build the outgoing AuthorizeRequest telegram for a given sequence number."""
    return Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(sequence),
        payload=apci.AuthorizeRequest(key=key),
    )


def _ack(ia: IndividualAddress, xknx: XKNX, sequence: int) -> Telegram:
    """Build an incoming TAck for a given sequence number."""
    return Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TAck(sequence),
    )


def _authorize_response(
    ia: IndividualAddress, xknx: XKNX, sequence: int, level: int
) -> Telegram:
    """Build an incoming AuthorizeResponse telegram for a given sequence number."""
    return Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(sequence),
        payload=apci.AuthorizeResponse(level=level),
    )


async def test_dmp_authorize_r_co_with_key(xknx_setup: XKNX) -> None:
    """Test dmp_authorize_r_co sends AuthorizeRequest and returns level."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    test_key = 0x12345678

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    task = asyncio.create_task(dmp_authorize_r_co(conn, test_key))
    await asyncio.sleep(0)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(_authorize_request(ia, 0, test_key))
    ]

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(_authorize_response(ia, xknx, 0, level=3))

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

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(_authorize_request(ia, 0, FREE_ACCESS_KEY))
    ]

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(_authorize_response(ia, xknx, 0, level=15))

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

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(_authorize_response(ia, xknx, 0, level=0))

    level = await task
    assert level == 0

    # only the free-access attempt - level 0 short-circuits the client key
    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(_authorize_request(ia, 0, FREE_ACCESS_KEY)),
        call(Telegram(destination_address=ia, tpci=tpci.TAck(0))),
    ]

    await conn.disconnect()


async def test_dmp_authorize2_r_co_client_key_is_better(xknx_setup: XKNX) -> None:
    """Test dmp_authorize2_r_co when client key gives better access than free."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    client_key = 0xABCDEF00

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond_to_requests() -> None:
        async with asyncio_timeout(RESPONDER_TIMEOUT):
            while xknx.cemi_handler.send_telegram.call_count < 1:  # noqa: ASYNC110
                await asyncio.sleep(0)
        xknx.management.process(_ack(ia, xknx, 0))
        xknx.management.process(_authorize_response(ia, xknx, 0, level=15))

        async with asyncio_timeout(RESPONDER_TIMEOUT):
            while xknx.cemi_handler.send_telegram.call_count < 3:  # noqa: ASYNC110
                await asyncio.sleep(0)
        xknx.management.process(_ack(ia, xknx, 1))
        xknx.management.process(_authorize_response(ia, xknx, 1, level=3))

    responder = asyncio.create_task(respond_to_requests())
    level = await dmp_authorize2_r_co(conn, client_key)
    await responder

    assert level == 3

    # free access (level 15) then client key (level 3) - client key wins, no re-auth
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _authorize_request(ia, 0, FREE_ACCESS_KEY),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _authorize_request(ia, 1, client_key),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
    ]

    await conn.disconnect()


async def test_dmp_authorize2_r_co_equal_levels(xknx_setup: XKNX) -> None:
    """Test dmp_authorize2_r_co when client key gives equal access to free — no re-auth."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    client_key = 0xABCDEF00

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond_to_requests() -> None:
        async with asyncio_timeout(RESPONDER_TIMEOUT):
            while xknx.cemi_handler.send_telegram.call_count < 1:  # noqa: ASYNC110
                await asyncio.sleep(0)
        xknx.management.process(_ack(ia, xknx, 0))
        xknx.management.process(_authorize_response(ia, xknx, 0, level=5))

        async with asyncio_timeout(RESPONDER_TIMEOUT):
            while xknx.cemi_handler.send_telegram.call_count < 3:  # noqa: ASYNC110
                await asyncio.sleep(0)
        xknx.management.process(_ack(ia, xknx, 1))
        xknx.management.process(_authorize_response(ia, xknx, 1, level=5))

    responder = asyncio.create_task(respond_to_requests())
    level = await dmp_authorize2_r_co(conn, client_key)
    await responder

    assert level == 5
    # 2 AuthorizeRequests (free, client) + 2 background ACKs for their
    # responses (see Management.process) - no third, re-authorizing request
    assert xknx.cemi_handler.send_telegram.call_count == 4
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _authorize_request(ia, 0, FREE_ACCESS_KEY),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _authorize_request(ia, 1, client_key),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
    ]

    await conn.disconnect()


async def test_dmp_authorize2_r_co_free_access_is_better(xknx_setup: XKNX) -> None:
    """Test dmp_authorize2_r_co when free access is better than client key."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    client_key = 0xABCDEF00

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond_to_requests() -> None:
        async with asyncio_timeout(RESPONDER_TIMEOUT):
            while xknx.cemi_handler.send_telegram.call_count < 1:  # noqa: ASYNC110
                await asyncio.sleep(0)
        xknx.management.process(_ack(ia, xknx, 0))
        xknx.management.process(_authorize_response(ia, xknx, 0, level=3))

        async with asyncio_timeout(RESPONDER_TIMEOUT):
            while xknx.cemi_handler.send_telegram.call_count < 3:  # noqa: ASYNC110
                await asyncio.sleep(0)
        xknx.management.process(_ack(ia, xknx, 1))
        xknx.management.process(_authorize_response(ia, xknx, 1, level=10))

        async with asyncio_timeout(RESPONDER_TIMEOUT):
            while xknx.cemi_handler.send_telegram.call_count < 5:  # noqa: ASYNC110
                await asyncio.sleep(0)
        xknx.management.process(_ack(ia, xknx, 2))
        xknx.management.process(_authorize_response(ia, xknx, 2, level=3))

    responder = asyncio.create_task(respond_to_requests())
    level = await dmp_authorize2_r_co(conn, client_key)
    await responder

    assert level == 3

    # free access (level 3) then client key (level 10, worse) - re-authorize with free access
    assert [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list] == [
        _authorize_request(ia, 0, FREE_ACCESS_KEY),
        Telegram(destination_address=ia, tpci=tpci.TAck(0)),
        _authorize_request(ia, 1, client_key),
        Telegram(destination_address=ia, tpci=tpci.TAck(1)),
        _authorize_request(ia, 2, FREE_ACCESS_KEY),
        Telegram(destination_address=ia, tpci=tpci.TAck(2)),
    ]

    await conn.disconnect()
