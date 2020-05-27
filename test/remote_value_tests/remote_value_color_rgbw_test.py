"""Unit test for RemoteValueColorRGBW objects."""
import asyncio
import unittest

import pytest
pytestmark = pytest.mark.asyncio

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueColorRGBW
from xknx.telegram import GroupAddress, Telegram


class TestRemoteValueColorRGBW(unittest.TestCase):
    """Test class for RemoteValueColorRGBW objects."""

    async def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx)
        input_list = [100, 101, 102, 127]
        input_tuple = (100, 101, 102, 127)
        expected = DPTArray((0x64, 0x65, 0x66, 0x7f, 0x00, 0x0f))
        self.assertEqual(remote_value.to_knx(input_tuple), expected)
        self.assertEqual(remote_value.to_knx(input_list), expected)
        self.assertEqual(remote_value.to_knx(input_tuple + (15,)), expected)
        self.assertEqual(remote_value.to_knx(input_list + [15]), expected)
        self.assertEqual(remote_value.to_knx(input_tuple + (0, 15)), expected)
        self.assertEqual(remote_value.to_knx(input_list + [0, 15]), expected)

    async def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx)
        self.assertEqual(
            remote_value.from_knx(DPTArray((0x64, 0x65, 0x66, 0x7f, 0x00, 0x00))),
            [0, 0, 0, 0])
        self.assertEqual(
            remote_value.from_knx(DPTArray((0x64, 0x65, 0x66, 0x7f, 0x00, 0x0f))),
            [100, 101, 102, 127])
        self.assertEqual(
            remote_value.from_knx(DPTArray((0x64, 0x65, 0x66, 0x7f, 0x00, 0x00))),
            [100, 101, 102, 127])
        self.assertEqual(
            remote_value.from_knx(DPTArray((0xff, 0x65, 0x66, 0xff, 0x00, 0x09))),
            [255, 101, 102, 255])
        self.assertEqual(
            remote_value.from_knx(DPTArray((0x64, 0x65, 0x66, 0x7f, 0x00, 0x01))),
            [255, 101, 102, 127])

    async def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(xknx)
        with self.assertRaises(ConversionError):
            remote_value.to_knx((101, 102, 103))
        with self.assertRaises(ConversionError):
            remote_value.to_knx((0, 0, 15, 101, 102, 103, 104))
        with self.assertRaises(ConversionError):
            remote_value.to_knx((256, 101, 102, 103))
        with self.assertRaises(ConversionError):
            remote_value.to_knx((100, 256, 102, 103))
        with self.assertRaises(ConversionError):
            remote_value.to_knx((100, 101, 256, 103))
        with self.assertRaises(ConversionError):
            remote_value.to_knx((100, 101, 102, 256))
        with self.assertRaises(ConversionError):
            remote_value.to_knx((100, -101, 102, 103))
        with self.assertRaises(ConversionError):
            remote_value.to_knx(("100", 101, 102, 103))
        with self.assertRaises(ConversionError):
            remote_value.to_knx("100, 101, 102, 103")

    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(
            xknx,
            group_address=GroupAddress("1/2/3"))
        await remote_value.set((100, 101, 102, 103))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTArray((0x64, 0x65, 0x66, 0x67, 0x00, 0x0f))))
        await remote_value.set((100, 101, 104, 105))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTArray((0x64, 0x65, 0x68, 0x69, 0x00, 0x0f))))

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTArray((0x64, 0x65, 0x66, 0x67, 0x00, 0x0f)))
        await remote_value.process(telegram)
        self.assertEqual(remote_value.value, [100, 101, 102, 103])

    async def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueColorRGBW(
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
                payload=DPTArray((0x64, 0x65, 0x66)))
            await remote_value.process(telegram)
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTArray((0x00, 0x00, 0x0f, 0x64, 0x65, 0x66, 0x67)))
            await remote_value.process(telegram)
