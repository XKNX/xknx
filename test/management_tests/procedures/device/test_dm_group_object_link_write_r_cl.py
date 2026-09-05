"""Tests for dm_group_object_link_write_r_cl — KNX v02.01.02 - Management Procedures 03.05.02 - §3.37.3."""

import asyncio
from unittest.mock import AsyncMock, call

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError
from xknx.management.procedures.device.dm_group_object_link_read_r_cl import (
    GroupObjectLink,
)
from xknx.management.procedures.device.dm_group_object_link_write_r_cl import (
    dm_group_object_link_write_r_cl,
)
from xknx.telegram import IndividualAddress, Telegram, TelegramDirection, apci, tpci
from xknx.telegram.address import GroupAddress


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


def _response(
    ia: IndividualAddress,
    xknx: XKNX,
    sequence: int,
    sending_address: int,
    start_index: int,
    group_address_list: list[GroupAddress],
) -> Telegram:
    """Build an incoming LinkResponse telegram."""
    return Telegram(
        source_address=ia,
        destination_address=xknx.current_address,
        direction=TelegramDirection.INCOMING,
        tpci=tpci.TDataConnected(sequence),
        payload=apci.LinkResponse(
            group_object_number=3,
            sending_address=sending_address,
            start_index=start_index,
            group_address_list=group_address_list,
        ),
    )


async def test_dm_group_object_link_write_r_cl_add() -> None:
    """Test adding a Group Address link, non-sending."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    ga = GroupAddress("1/1/1")
    task = asyncio.create_task(
        dm_group_object_link_write_r_cl(conn, group_object_number=3, group_address=ga)
    )
    await asyncio.sleep(0)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(
            Telegram(
                destination_address=ia,
                tpci=tpci.TDataConnected(0),
                payload=apci.LinkWrite(
                    group_object_number=3,
                    group_address=ga,
                    delete=False,
                    sending=False,
                ),
            )
        )
    ]

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _response(
            ia, xknx, 0, sending_address=0, start_index=1, group_address_list=[ga]
        )
    )

    result = await task
    assert result == GroupObjectLink(sending_address=0, group_addresses=[ga])

    await conn.disconnect()


async def test_dm_group_object_link_write_r_cl_add_as_sending() -> None:
    """Test adding a Group Address link as the sending address."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    ga = GroupAddress("1/1/1")
    task = asyncio.create_task(
        dm_group_object_link_write_r_cl(
            conn, group_object_number=3, group_address=ga, sending=True
        )
    )
    await asyncio.sleep(0)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(
            Telegram(
                destination_address=ia,
                tpci=tpci.TDataConnected(0),
                payload=apci.LinkWrite(
                    group_object_number=3,
                    group_address=ga,
                    delete=False,
                    sending=True,
                ),
            )
        )
    ]

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _response(
            ia, xknx, 0, sending_address=1, start_index=1, group_address_list=[ga]
        )
    )

    result = await task
    assert result == GroupObjectLink(sending_address=1, group_addresses=[ga])

    await conn.disconnect()


async def test_dm_group_object_link_write_r_cl_delete() -> None:
    """Test removing a Group Address link."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    ga = GroupAddress("1/1/1")
    task = asyncio.create_task(
        dm_group_object_link_write_r_cl(
            conn, group_object_number=3, group_address=ga, delete=True
        )
    )
    await asyncio.sleep(0)

    assert xknx.cemi_handler.send_telegram.call_args_list == [
        call(
            Telegram(
                destination_address=ia,
                tpci=tpci.TDataConnected(0),
                payload=apci.LinkWrite(
                    group_object_number=3,
                    group_address=ga,
                    delete=True,
                    sending=False,
                ),
            )
        )
    ]

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _response(ia, xknx, 0, sending_address=0, start_index=1, group_address_list=[])
    )

    result = await task
    assert result == GroupObjectLink(sending_address=0, group_addresses=[])

    await conn.disconnect()


async def test_dm_group_object_link_write_r_cl_negative_response_raises() -> None:
    """Test the procedure raises ManagementConnectionError on a negative A_Link_Response."""
    xknx = _xknx_setup()
    ia = IndividualAddress("4.0.10")

    conn = await xknx.management.connect(ia)
    xknx.cemi_handler.send_telegram.reset_mock()

    ga = GroupAddress("1/1/1")
    task = asyncio.create_task(
        dm_group_object_link_write_r_cl(conn, group_object_number=3, group_address=ga)
    )
    await asyncio.sleep(0)

    xknx.management.process(_ack(ia, xknx, 0))
    xknx.management.process(
        _response(ia, xknx, 0, sending_address=0, start_index=0, group_address_list=[])
    )

    with pytest.raises(ManagementConnectionError, match=r"negative A_Link_Response"):
        await task

    await conn.disconnect()
