"""Unit test for RemoteValueString objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary, DPTLatin1, DPTString
from xknx.exceptions import ConversionError
from xknx.remote_value import RemoteValueString
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueWrite


class TestRemoteValueString:
    """Test class for RemoteValueString objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        dpt_array_string = DPTArray(
            (
                0x4B,
                0x4E,
                0x58,
                0x20,
                0x69,
                0x73,
                0x20,
                0x4F,
                0x4B,
                0x00,
                0x00,
                0x00,
                0x00,
                0x00,
            )
        )
        remote_value_default = RemoteValueString(xknx)
        assert remote_value_default.dpt_class == DPTString
        assert remote_value_default.to_knx("KNX is OK") == dpt_array_string

        remote_value_ascii = RemoteValueString(xknx, value_type="string")
        assert remote_value_ascii.dpt_class == DPTString
        assert remote_value_ascii.to_knx("KNX is OK") == dpt_array_string

        remote_value_latin1 = RemoteValueString(xknx, value_type="latin_1")
        assert remote_value_latin1.dpt_class == DPTLatin1
        assert remote_value_latin1.to_knx("KNX is OK") == dpt_array_string

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueString(xknx)
        assert (
            remote_value.from_knx(
                DPTArray(
                    (
                        0x4B,
                        0x4E,
                        0x58,
                        0x20,
                        0x69,
                        0x73,
                        0x20,
                        0x4F,
                        0x4B,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                        0x00,
                    )
                )
            )
            == "KNX is OK"
        )

    def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueString(xknx)
        with pytest.raises(ConversionError):
            remote_value.to_knx("123456789012345")

    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueString(xknx, group_address=GroupAddress("1/2/3"))
        await remote_value.set("asdf")
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(
                DPTArray((97, 115, 100, 102, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
            ),
        )
        await remote_value.set("ASDF")
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(
                DPTArray((65, 83, 68, 70, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
            ),
        )

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueString(xknx, group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(
                DPTArray(
                    (
                        0x41,
                        0x41,
                        0x41,
                        0x41,
                        0x41,
                        0x42,
                        0x42,
                        0x42,
                        0x42,
                        0x42,
                        0x43,
                        0x43,
                        0x43,
                        0x43,
                    )
                )
            ),
        )
        await remote_value.process(telegram)
        assert remote_value.value == "AAAAABBBBBCCCC"

    async def test_to_process_error(self):
        """Test process erroneous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueString(xknx, group_address=GroupAddress("1/2/3"))

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        assert await remote_value.process(telegram) is False

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((0x64, 0x65))),
        )
        assert await remote_value.process(telegram) is False

        assert remote_value.value is None
