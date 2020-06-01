"""Unit test for RemoteValue1Count objects."""
import asyncio
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import CouldNotParseTelegram
from xknx.remote_value import RemoteValue1Count
from xknx.telegram import GroupAddress, Telegram

from xknx._test import Testcase

class TestRemoteValue1Count(Testcase):
    """Test class for RemoteValue1Count objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValue1Count(xknx)
        self.assertEqual(remote_value.to_knx(100), DPTArray((0x64, )))

    @pytest.mark.asyncio
    async def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValue1Count(xknx)
        self.assertEqual(remote_value.from_knx(DPTArray((0x64, ))), 100)

    @pytest.mark.asyncio
    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValue1Count(
            xknx,
            group_address=GroupAddress("1/2/3"))
        await remote_value.set(100)
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTArray((0x64, ))))
        await remote_value.set(101, )
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTArray((0x65, ))))

    @pytest.mark.asyncio
    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValue1Count(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTArray((0x64, )))
        await remote_value.process(telegram)
        self.assertEqual(remote_value.value, 100)

    @pytest.mark.asyncio
    async def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX()
        remote_value = RemoteValue1Count(
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
