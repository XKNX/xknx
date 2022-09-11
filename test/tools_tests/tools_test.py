"""Test xknx tools package."""
from unittest.mock import patch

from xknx import XKNX
from xknx.dpt.dpt import DPTArray, DPTBinary
from xknx.telegram import GroupAddress, Telegram, TelegramDirection, apci
from xknx.tools import (
    group_value_read,
    group_value_response,
    group_value_write,
    read_group_value,
)


async def test_group_value_read():
    """Test group_value_read."""
    xknx = XKNX()
    group_address = "1/2/3"

    read = Telegram(
        destination_address=GroupAddress(group_address),
        payload=apci.GroupValueRead(),
    )
    await group_value_read(xknx, "1/2/3")
    assert xknx.telegrams.qsize() == 1
    assert xknx.telegrams.get_nowait() == read


async def test_group_value_response():
    """Test group_value_response."""
    xknx = XKNX()
    group_address = "1/2/3"

    response = Telegram(
        destination_address=GroupAddress(group_address),
        payload=apci.GroupValueResponse(DPTBinary(1)),
    )
    await group_value_response(xknx, "1/2/3", True)
    assert xknx.telegrams.qsize() == 1
    assert xknx.telegrams.get_nowait() == response


async def test_group_value_write():
    """Test group_value_write."""
    xknx = XKNX()
    group_address = "1/2/3"

    write = Telegram(
        destination_address=GroupAddress(group_address),
        payload=apci.GroupValueWrite(DPTArray([0x80])),
    )
    await group_value_write(xknx, "1/2/3", 50, value_type="percent")
    assert xknx.telegrams.qsize() == 1
    assert xknx.telegrams.get_nowait() == write


@patch("xknx.core.value_reader.ValueReader.read")
async def test_read_group_value(value_reader_read_mock):
    """Test read_group_value."""
    xknx = XKNX()
    test_group_address = GroupAddress("1/2/3")

    response_telegram = Telegram(
        destination_address=test_group_address,
        direction=TelegramDirection.INCOMING,
        payload=apci.GroupValueResponse(DPTArray((0x0C, 0x00))),
    )
    value_reader_read_mock.return_value = response_telegram

    response_value = await read_group_value(xknx, "1/2/3", value_type="temperature")
    # GroupValueRead telegram is not in queue because ValueReader.read is mocked.
    # This is tested in ValueReader tests.
    assert response_value == 20.48
