"""Tests for dm_group_object_link_read_r_cl — KNX v02.01.02 - Management Procedures 03.05.02 - §3.37.2."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dm_group_object_link_read_r_cl import (
    GroupObjectLink,
    dm_group_object_link_read_r_cl,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci
from xknx.telegram.address import GroupAddress

RESPONDER_TIMEOUT = 1


@pytest.fixture(name="xknx_setup")
def fixture_xknx_setup() -> XKNX:
    """Set up XKNX with mocked cemi_handler."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    return xknx


def _respond(
    xknx: XKNX,
    ia: IndividualAddress,
    seq: int,
    group_object_number: int,
    sending_address: int,
    start_index: int,
    group_address_list: list[GroupAddress],
) -> None:
    """Inject ACK + LinkResponse into the management layer."""
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
            payload=apci.LinkResponse(
                group_object_number=group_object_number,
                sending_address=sending_address,
                start_index=start_index,
                group_address_list=group_address_list,
            ),
        )
    )


async def _wait_for_request(xknx: XKNX, req_num: int) -> None:
    """Wait until the req_num-th request telegram has been sent (1-indexed)."""
    threshold = req_num * 2 - 1
    async with asyncio.timeout(RESPONDER_TIMEOUT):
        while xknx.cemi_handler.send_telegram.call_count < threshold:  # noqa: ASYNC110
            await asyncio.sleep(0)


async def test_dm_group_object_link_read_r_cl_single_chunk(xknx_setup: XKNX) -> None:
    """Test reading a Group Object with fewer than 6 linked Group Addresses (single request)."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    gas = [GroupAddress("1/1/1"), GroupAddress("1/1/2")]

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _respond(
            xknx, ia, 0, 3, sending_address=1, start_index=1, group_address_list=gas
        )

    responder = asyncio.create_task(respond())
    result = await dm_group_object_link_read_r_cl(conn, group_object_number=3)
    await responder

    assert result == GroupObjectLink(sending_address=1, group_addresses=gas)
    assert xknx.cemi_handler.send_telegram.call_args_list[0].args[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(0),
        payload=apci.LinkRead(group_object_number=3, start_index=1),
    )
    await conn.disconnect()


async def test_dm_group_object_link_read_r_cl_negative_response_first_request(
    xknx_setup: XKNX,
) -> None:
    """Test a negative response on the very first request returns an empty GroupObjectLink, not an error."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _respond(
            xknx, ia, 0, 3, sending_address=0, start_index=0, group_address_list=[]
        )

    responder = asyncio.create_task(respond())
    result = await dm_group_object_link_read_r_cl(conn, group_object_number=3)
    await responder

    assert result == GroupObjectLink(sending_address=0, group_addresses=[])
    await conn.disconnect()


async def test_dm_group_object_link_read_r_cl_multiple_chunks(xknx_setup: XKNX) -> None:
    """Test reading continues at start_index 7 when the first response carries a full 6 Group Addresses."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    chunk_1 = [GroupAddress(f"1/1/{i}") for i in range(1, 7)]
    chunk_2 = [GroupAddress("1/1/7")]

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _respond(
            xknx, ia, 0, 3, sending_address=2, start_index=1, group_address_list=chunk_1
        )
        await _wait_for_request(xknx, 2)
        _respond(
            xknx, ia, 1, 3, sending_address=2, start_index=7, group_address_list=chunk_2
        )

    responder = asyncio.create_task(respond())
    result = await dm_group_object_link_read_r_cl(conn, group_object_number=3)
    await responder

    assert result == GroupObjectLink(
        sending_address=2, group_addresses=chunk_1 + chunk_2
    )
    assert xknx.cemi_handler.send_telegram.call_args_list[2].args[0] == Telegram(
        destination_address=ia,
        tpci=tpci.TDataConnected(1),
        payload=apci.LinkRead(group_object_number=3, start_index=7),
    )
    await conn.disconnect()


async def test_dm_group_object_link_read_r_cl_exact_multiple_of_six(
    xknx_setup: XKNX,
) -> None:
    """Test a Group Object with exactly 6 linked Group Addresses ends via the negative response, not an error."""
    xknx = xknx_setup
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    chunk_1 = [GroupAddress(f"1/1/{i}") for i in range(1, 7)]

    async def respond() -> None:
        await _wait_for_request(xknx, 1)
        _respond(
            xknx, ia, 0, 3, sending_address=1, start_index=1, group_address_list=chunk_1
        )
        await _wait_for_request(xknx, 2)
        _respond(
            xknx, ia, 1, 3, sending_address=0, start_index=0, group_address_list=[]
        )

    responder = asyncio.create_task(respond())
    result = await dm_group_object_link_read_r_cl(conn, group_object_number=3)
    await responder

    assert result == GroupObjectLink(sending_address=1, group_addresses=chunk_1)
    await conn.disconnect()


async def _read_with_responses(
    xknx: XKNX, responses: list[tuple[int, int, list[GroupAddress]]]
) -> GroupObjectLink:
    """Run the procedure, answering each request with (group object, start_index, GAs)."""
    ia = IndividualAddress("4.0.10")
    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    async def respond() -> None:
        for req_num, (group_object_number, start_index, gas) in enumerate(
            responses, start=1
        ):
            await _wait_for_request(xknx, req_num)
            _respond(
                xknx,
                ia,
                req_num - 1,
                group_object_number,
                sending_address=1,
                start_index=start_index,
                group_address_list=gas,
            )

    responder = asyncio.create_task(respond())
    try:
        return await dm_group_object_link_read_r_cl(conn, group_object_number=3)
    finally:
        await responder
        await conn.disconnect()


def _gas(first: int, last: int) -> list[GroupAddress]:
    """Group Addresses 1/1/first to 1/1/last."""
    return [GroupAddress(f"1/1/{i}") for i in range(first, last + 1)]


async def test_dm_group_object_link_read_r_cl_exactly_eighteen(
    xknx_setup: XKNX,
) -> None:
    """
    Test a Group Object with exactly 18 linked Group Addresses is read completely.

    After three full chunks (1, 7, 13) the probe at start_index 15 returns
    entries 15-18 - 4 addresses, so there is no 19th.
    """
    result = await _read_with_responses(
        xknx_setup,
        [
            (3, 1, _gas(1, 6)),
            (3, 7, _gas(7, 12)),
            (3, 13, _gas(13, 18)),
            (3, 15, _gas(15, 18)),
        ],
    )
    assert result.group_addresses == _gas(1, 18)
    sent = [
        call.args[0].payload.start_index
        for call in xknx_setup.cemi_handler.send_telegram.call_args_list
        if isinstance(call.args[0].payload, apci.LinkRead)
    ]
    assert sent == [1, 7, 13, 15]


async def test_dm_group_object_link_read_r_cl_eighteen_probe_negative(
    xknx_setup: XKNX,
) -> None:
    """Test a negative response to the start_index 15 probe also means the 18 are complete."""
    result = await _read_with_responses(
        xknx_setup,
        [(3, 1, _gas(1, 6)), (3, 7, _gas(7, 12)), (3, 13, _gas(13, 18)), (3, 0, [])],
    )
    assert result.group_addresses == _gas(1, 18)


async def test_dm_group_object_link_read_r_cl_more_than_eighteen_raises(
    xknx_setup: XKNX,
) -> None:
    """Test the probe at start_index 15 returning more than 4 addresses raises."""
    with pytest.raises(
        ManagementConnectionError, match=r"more than 18 Group Addresses linked"
    ):
        await _read_with_responses(
            xknx_setup,
            [
                (3, 1, _gas(1, 6)),
                (3, 7, _gas(7, 12)),
                (3, 13, _gas(13, 18)),
                (3, 15, _gas(15, 19)),
            ],
        )


@pytest.mark.parametrize(
    ("response", "match"),
    [
        ((4, 1, _gas(1, 2)), r"A_Link_Response for group object 4 does not match"),
        ((3, 2, _gas(1, 2)), r"start_index 2 does not match request \(1\)"),
    ],
)
async def test_dm_group_object_link_read_r_cl_echo_mismatch(
    xknx_setup: XKNX,
    response: tuple[int, int, list[GroupAddress]],
    match: str,
) -> None:
    """Test a response echoing a different group object or start_index raises."""
    with pytest.raises(ManagementConnectionError, match=match):
        await _read_with_responses(xknx_setup, [response])
