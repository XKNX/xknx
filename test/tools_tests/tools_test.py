"""Test xknx tools package."""
from unittest.mock import patch

import pytest

from xknx import XKNX
from xknx.devices import NumericValue
from xknx.dpt import DPTArray, DPTBinary, DPTTemperature
from xknx.exceptions import ConversionError
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


@pytest.mark.parametrize(
    "value,value_type,expected",
    [
        (50, "percent", DPTArray((0x80,))),
        (True, None, DPTBinary(1)),
        (False, None, DPTBinary(0)),
        (20.48, DPTTemperature, DPTArray((0x0C, 0x00))),
        (-100, 6, DPTArray((0x9C,))),
        ((0x0C, 0x00), None, DPTArray((0x0C, 0x00))),
        (DPTBinary(1), None, DPTBinary(1)),
    ],
)
async def test_group_value_write(value, value_type, expected):
    """Test group_value_write."""
    xknx = XKNX()
    group_address = "1/2/3"

    write = Telegram(
        destination_address=GroupAddress(group_address),
        payload=apci.GroupValueWrite(expected),
    )
    await group_value_write(xknx, "1/2/3", value, value_type=value_type)
    assert xknx.telegrams.qsize() == 1
    assert xknx.telegrams.get_nowait() == write


@pytest.mark.parametrize(
    "value,value_type,error_type",
    [
        (50, "unknown", ValueError),
        (50, 9.001, ValueError),  # float is invalid
        (101, "percent", ConversionError),  # too big
    ],
)
async def test_group_value_write_invalid(value, value_type, error_type):
    """Test group_value_write."""
    xknx = XKNX()
    with pytest.raises(error_type):
        await group_value_write(xknx, "1/2/3", value, value_type=value_type)


@pytest.mark.parametrize(
    "value,value_type,expected",
    [
        (50, "percent", DPTArray((0x80,))),
        ((0x80,), None, DPTArray((0x80,))),
        (True, None, DPTBinary(1)),
    ],
)
@patch("xknx.core.value_reader.ValueReader.read")
async def test_read_group_value(value_reader_read_mock, value, value_type, expected):
    """Test read_group_value."""
    xknx = XKNX()
    test_group_address = "1/2/3"

    response_telegram = Telegram(
        destination_address=GroupAddress(test_group_address),
        direction=TelegramDirection.INCOMING,
        payload=apci.GroupValueResponse(expected),
    )
    value_reader_read_mock.return_value = response_telegram

    response_value = await read_group_value(
        xknx, test_group_address, value_type=value_type
    )
    # GroupValueRead telegram is not in queue because ValueReader.read is mocked.
    # This is tested in ValueReader tests.
    assert response_value == value


async def test_tools_with_internal_addresses():
    """Test tools using internal addresses."""
    with patch("xknx.io.knxip_interface.KNXIPInterface.start"):
        xknx = XKNX()
        await xknx.start()

    internal_address = "i-test"
    test_type = "1byte_unsigned"
    number = NumericValue(
        xknx,
        "Test",
        group_address=internal_address,
        value_type=test_type,
        respond_to_read=True,
    )

    assert number.resolve_state() is None
    await group_value_write(xknx, internal_address, 1, value_type=test_type)
    await xknx.telegrams.join()
    assert number.resolve_state() == 1

    response_value = await read_group_value(
        xknx, internal_address, value_type=test_type
    )
    assert response_value == 1
    await xknx.stop()
