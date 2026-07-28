"""Tests for the host-agnostic xknx MCP tool functions."""

from enum import Enum
from unittest.mock import MagicMock, patch

import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseAddress
from xknx.mcp import (
    DecodeDptPayloadInput,
    DptFilter,
    EncodeDptPayloadInput,
    GroupAddressInput,
    GroupValueReadInput,
    GroupValueWriteInput,
    decode_dpt_payload,
    describe_dpt,
    encode_dpt_payload,
    get_connection_status,
    list_dpts,
    read_group_value,
    send_group_value_read,
    send_group_value_write,
)
from xknx.mcp.tools import _jsonify
from xknx.telegram import GroupAddress, Telegram, TelegramDirection, apci


async def test_list_dpts_unfiltered() -> None:
    """Without a filter the full DPT catalogue is returned, sorted by DPT number."""
    result = await list_dpts()
    assert result.total_count > 100
    numbers = [d.dpt for d in result.dpts]
    assert numbers == sorted(numbers, key=lambda s: [int(p or 0) for p in s.split(".")])
    assert "9.001" in numbers


async def test_list_dpts_text_filter() -> None:
    """The text filter keeps only DPTs whose number/value type/unit matches."""
    result = await list_dpts(DptFilter(text="temperature"))
    assert result.total_count > 0
    assert "9.001" in {d.dpt for d in result.dpts}
    assert all("temperature" in (d.value_type or "") for d in result.dpts)


def test_jsonify_shapes() -> None:
    """_jsonify passes JSON natives through, flattens tuples and stringifies the rest."""

    class _Mode(Enum):
        AUTO = "auto"

    assert _jsonify(21.5) == 21.5
    assert _jsonify(None) is None
    assert _jsonify((0x0C, 0x00)) == [0x0C, 0x00]
    assert _jsonify(_Mode.AUTO) == str(_Mode.AUTO)


async def test_list_dpts_main_filter_and_pagination() -> None:
    """A main filter restricts subtypes; a limit truncates and flags overflow."""
    only_main_1 = await list_dpts(DptFilter(main=1))
    assert only_main_1.total_count > 1
    assert all(d.dpt.split(".")[0] == "1" for d in only_main_1.dpts)

    page = await list_dpts(DptFilter(main=1, limit=3))
    assert len(page.dpts) == 3
    assert page.limit_reached
    # Pagination is self-describing: next_offset points past the returned window.
    assert page.offset == 0
    assert page.next_offset == 3
    last = await list_dpts(DptFilter(main=1, limit=1000))
    assert last.next_offset is None


async def test_describe_dpt_by_number_and_name() -> None:
    """A DPT resolves by number and by value-type name, exposing units/bounds."""
    by_number = await describe_dpt("9.001")
    assert by_number.found
    assert by_number.dpt is not None
    assert by_number.dpt.value_type == "temperature"
    assert by_number.dpt.unit == "°C"
    assert by_number.dpt.value_min is not None

    by_name = await describe_dpt("temperature")
    assert by_name.found
    assert by_name.dpt is not None
    assert by_name.dpt.dpt == "9.001"


async def test_describe_dpt_unknown() -> None:
    """An unknown identifier returns a not-found result."""
    result = await describe_dpt("999.999")
    assert not result.found
    assert result.dpt is None


async def test_get_connection_status_disconnected() -> None:
    """A freshly constructed XKNX reports a disconnected state."""
    status = await get_connection_status(XKNX())
    assert status.state == "DISCONNECTED"
    assert not status.connected
    assert status.connection_type is None
    assert status.connected_since is None
    assert status.local_address == "0.0.0"


async def test_send_group_value_read_queues_telegram() -> None:
    """A GroupValueRead is queued for the requested address."""
    xknx = XKNX()
    result = await send_group_value_read(xknx, GroupAddressInput(group_address="1/2/3"))
    assert result.apci == "GroupValueRead"
    assert xknx.telegrams.qsize() == 1
    assert xknx.telegrams.get_nowait() == Telegram(
        destination_address=GroupAddress("1/2/3"), payload=apci.GroupValueRead()
    )


async def test_send_group_value_write_encodes_and_queues() -> None:
    """A GroupValueWrite encodes the value with the given DPT and is queued."""
    xknx = XKNX()
    result = await send_group_value_write(
        xknx, GroupValueWriteInput(group_address="1/2/3", value=50, value_type="percent")
    )
    assert result.apci == "GroupValueWrite"
    assert xknx.telegrams.qsize() == 1
    assert xknx.telegrams.get_nowait() == Telegram(
        destination_address=GroupAddress("1/2/3"),
        payload=apci.GroupValueWrite(DPTArray((0x80,))),
    )


async def test_send_group_value_write_invalid_address() -> None:
    """An unparsable group address is rejected before anything is queued."""
    xknx = XKNX()
    with pytest.raises(CouldNotParseAddress):
        await send_group_value_write(
            xknx, GroupValueWriteInput(group_address="not-an-address", value=1)
        )
    assert xknx.telegrams.qsize() == 0


@patch("xknx.core.value_reader.ValueReader.read")
async def test_read_group_value_decodes_response(read_mock: MagicMock) -> None:
    """A response is decoded with the requested DPT and reported as responded."""
    xknx = XKNX()
    read_mock.return_value = Telegram(
        destination_address=GroupAddress("1/2/3"),
        direction=TelegramDirection.INCOMING,
        payload=apci.GroupValueResponse(DPTArray((0x80,))),
    )
    result = await read_group_value(
        xknx, GroupValueReadInput(group_address="1/2/3", value_type="percent")
    )
    assert result.responded
    assert result.value == 50
    assert result.value_type == "percent"


@patch("xknx.core.value_reader.ValueReader.read")
async def test_read_group_value_no_response(read_mock: MagicMock) -> None:
    """When no device answers, the result is flagged as not responded."""
    xknx = XKNX()
    read_mock.return_value = None
    result = await read_group_value(
        xknx, GroupValueReadInput(group_address="1/2/3")
    )
    assert not result.responded
    assert result.value is None


async def test_read_group_value_raw_binary() -> None:
    """A raw (undecoded) DPTBinary response is coerced to its integer value."""
    xknx = XKNX()
    with patch("xknx.core.value_reader.ValueReader.read") as read_mock:
        read_mock.return_value = Telegram(
            destination_address=GroupAddress("1/2/3"),
            direction=TelegramDirection.INCOMING,
            payload=apci.GroupValueResponse(DPTBinary(1)),
        )
        result = await read_group_value(
            xknx, GroupValueReadInput(group_address="1/2/3")
        )
    assert result.value == 1


async def test_encode_dpt_payload() -> None:
    """encode_dpt_payload encodes a python value into raw bytes list using DPT."""
    # Test DPT 9.001 (temperature, DPTArray)
    temp_result = await encode_dpt_payload(EncodeDptPayloadInput(value=21.0, value_type="9.001"))
    assert temp_result.payload == [0x0C, 0x1A]
    assert temp_result.value_type == "9.001"

    # Test DPT 1.001 (switch, DPTBinary)
    switch_result = await encode_dpt_payload(EncodeDptPayloadInput(value=True, value_type="1.001"))
    assert switch_result.payload == [1]
    assert switch_result.value_type == "1.001"


async def test_decode_dpt_payload() -> None:
    """decode_dpt_payload decodes raw payload bytes list or int into python value using DPT."""
    # Test DPT 9.001 (DPTArray)
    temp_result = await decode_dpt_payload(DecodeDptPayloadInput(payload=[0x0C, 0x1A], value_type="9.001"))
    assert temp_result.value == 21.0
    assert temp_result.value_type == "9.001"

    # Test DPT 1.001 (DPTBinary)
    switch_result = await decode_dpt_payload(DecodeDptPayloadInput(payload=[1], value_type="1.001"))
    assert switch_result.value == "Switch.ON"
    assert switch_result.value_type == "1.001"

    # Test DPT 1.001 with integer payload directly
    switch_int_result = await decode_dpt_payload(DecodeDptPayloadInput(payload=1, value_type="1.001"))
    assert switch_int_result.value == "Switch.ON"

    # An empty payload for a 6-bit (DPTBinary) DPT is rejected.
    with pytest.raises(ValueError, match="Empty payload"):
        await decode_dpt_payload(DecodeDptPayloadInput(payload=[], value_type="1.001"))


