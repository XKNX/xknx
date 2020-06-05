"""Unit test for RemoteValueDptValue1Ucount objects."""
import asyncio
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueDptValue1Ucount
from xknx.telegram import GroupAddress, Telegram

from xknx._test import Testcase

class TestRemoteValueDptValue1Ucount(Testcase):
    """Test class for RemoteValueDptValue1Ucount objects."""

    @pytest.mark.asyncio
    async def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueDptValue1Ucount(xknx)
        self.assertEqual(remote_value.to_knx(10), DPTArray((0x0A, )))

    @pytest.mark.asyncio
    async def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueDptValue1Ucount(xknx)
        self.assertEqual(remote_value.from_knx(DPTArray((0x0A, ))), 10)

    @pytest.mark.asyncio
    async def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueDptValue1Ucount(xknx)
        with self.assertRaises(ConversionError):
            remote_value.to_knx(256)
        with self.assertRaises(ConversionError):
            remote_value.to_knx("256")

    @pytest.mark.asyncio
    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueDptValue1Ucount(
            xknx,
            group_address=GroupAddress("1/2/3"))
        await remote_value.set(10)
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = await xknx.telegrams.get()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTArray((0x0A, ))))
        await remote_value.set(11)
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = await xknx.telegrams.get()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTArray((0x0B, ))))

    @pytest.mark.asyncio
    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueDptValue1Ucount(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTArray((0x0A, )))
        await remote_value.process(telegram)
        self.assertEqual(remote_value.value, 10)

    @pytest.mark.asyncio
    async def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueDptValue1Ucount(
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
