"""Tests for nm_object_index_read — KNX v02.01.02 - Management Procedures 03.05.02 - §2.23.4 NM_ObjectIndex_Read."""

import asyncio
from unittest.mock import AsyncMock

import pytest

from xknx import XKNX
from xknx.exceptions import ManagementConnectionError, ManagementConnectionTimeout
from xknx.management.management import MANAGEMENT_CONNECTION_TIMEOUT
from xknx.management.procedures.network.nm_object_index_read import (
    nm_object_index_read,
)
from xknx.telegram import IndividualAddress, Telegram, apci, tpci

from ....conftest import EventLoopClockAdvancer

COUPLER = IndividualAddress("1.2.0")


def _answer(object_type: int, property_id: int, data: bytes) -> Telegram:
    """Return an answer of the device."""
    return Telegram(
        source_address=COUPLER,
        destination_address=IndividualAddress(0),
        tpci=tpci.TDataIndividual(),
        payload=apci.NetworkParameterResponse(
            object_type=object_type, property_id=property_id, test_info_and_result=data
        ),
    )


async def test_read(time_travel: EventLoopClockAdvancer) -> None:
    """Test the indexes of the instances are read connectionless."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    task = asyncio.create_task(
        nm_object_index_read(xknx, COUPLER, 6, start_instance=2, number_of_instances=1)
    )
    await asyncio.sleep(0)
    (sent,) = [c.args[0] for c in xknx.cemi_handler.send_telegram.call_args_list]
    assert sent.destination_address == COUPLER
    assert sent.tpci == tpci.TDataIndividual()
    assert sent.payload == apci.NetworkParameterRead(
        object_type=6, property_id=29, test_info=b"\x02\x01"
    )
    # an answer for another property, then the one asked for
    xknx.management.process(_answer(6, 30, b"\x02\x01\x07"))
    xknx.management.process(_answer(6, 29, b"\x02\x01\x07"))
    assert await task == [7]


async def test_no_answer(time_travel: EventLoopClockAdvancer) -> None:
    """Test a device that doesn't answer."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    task = asyncio.create_task(nm_object_index_read(xknx, COUPLER, 6))
    await asyncio.sleep(0)
    await time_travel(MANAGEMENT_CONNECTION_TIMEOUT)
    with pytest.raises(ManagementConnectionTimeout):
        await task


async def test_invalid_answer(time_travel: EventLoopClockAdvancer) -> None:
    """Test an answer without the test info."""
    xknx = XKNX()
    xknx.cemi_handler = AsyncMock()
    task = asyncio.create_task(nm_object_index_read(xknx, COUPLER, 6))
    await asyncio.sleep(0)
    xknx.management.process(_answer(6, 29, b"\x01"))
    with pytest.raises(ManagementConnectionError, match="Invalid object index"):
        await task
