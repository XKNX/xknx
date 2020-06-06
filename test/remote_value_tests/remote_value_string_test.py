"""Unit test for RemoteValueString objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueString
from xknx.telegram import GroupAddress, Telegram

from xknx._test import Testcase

class TestRemoteValueString(Testcase):
    """Test class for RemoteValueString objects."""

    @pytest.mark.anyio
    async def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueString(xknx)
        self.assertEqual(remote_value.to_knx("KNX is OK"), DPTArray((0x4B, 0x4E, 0x58, 0x20, 0x69,
                                                                     0x73, 0x20, 0x4F, 0x4B, 0x00,
                                                                     0x00, 0x00, 0x00, 0x00)))

    @pytest.mark.anyio
    async def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueString(xknx)
        self.assertEqual(remote_value.from_knx(DPTArray((0x4B, 0x4E, 0x58, 0x20, 0x69,
                                                         0x73, 0x20, 0x4F, 0x4B, 0x00,
                                                         0x00, 0x00, 0x00, 0x00))), "KNX is OK")

    @pytest.mark.anyio
    async def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueString(xknx)
        with self.assertRaises(ConversionError):
            remote_value.to_knx("123456789012345")

    @pytest.mark.anyio
    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueString(
            xknx,
            group_address=GroupAddress("1/2/3"))
        await remote_value.set("asdf")
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        telegram = await xknx.telegrams_out.q.get()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTArray((97, 115, 100, 102, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))))
        await remote_value.set("ASDF")
        self.assertEqual(xknx.telegrams_out.qsize(), 1)
        telegram = await xknx.telegrams_out.q.get()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTArray((65, 83, 68, 70, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))))

    @pytest.mark.anyio
    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueString(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTArray((0x41, 0x41, 0x41, 0x41, 0x41,
                              0x42, 0x42, 0x42, 0x42, 0x42,
                              0x43, 0x43, 0x43, 0x43)))
        await remote_value.process(telegram)
        self.assertEqual(remote_value.value, "AAAAABBBBBCCCC")

    @pytest.mark.anyio
    async def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueString(
            xknx,
            group_address=GroupAddress("1/2/3"))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTBinary(1))
            await remote_value.process(telegram)
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTArray((0x64, 0x65, )))
            await remote_value.process(telegram)
