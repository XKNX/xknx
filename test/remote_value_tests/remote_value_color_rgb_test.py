"""Unit test for RemoteValueColorRGB objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueColorRGB
from xknx.telegram import GroupAddress, Telegram


class TestRemoteValueColorRGB(unittest.TestCase):
    """Test class for RemoteValueColorRGB objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueColorRGB(xknx)
        self.assertEqual(remote_value.to_knx((100, 101, 102)), DPTArray((0x64, 0x65, 0x66)))
        self.assertEqual(remote_value.to_knx([100, 101, 102]), DPTArray((0x64, 0x65, 0x66)))

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueColorRGB(xknx)
        self.assertEqual(remote_value.from_knx(DPTArray((0x64, 0x65, 0x66))), (100, 101, 102))

    def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueColorRGB(xknx)
        with self.assertRaises(ConversionError):
            remote_value.to_knx((100, 101, 102, 103))
        with self.assertRaises(ConversionError):
            remote_value.to_knx((100, 101, 256))
        with self.assertRaises(ConversionError):
            remote_value.to_knx((100, -101, 102))
        with self.assertRaises(ConversionError):
            remote_value.to_knx(("100", 101, 102))
        with self.assertRaises(ConversionError):
            remote_value.to_knx("100, 101, 102")

    def test_set(self):
        """Test setting value."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueColorRGB(
            xknx,
            group_address=GroupAddress("1/2/3"))
        self.loop.run_until_complete(asyncio.Task(remote_value.set((100, 101, 102))))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTArray((0x64, 0x65, 0x66))))
        self.loop.run_until_complete(asyncio.Task(remote_value.set((100, 101, 104))))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTArray((0x64, 0x65, 0x68))))

    def test_process(self):
        """Test process telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueColorRGB(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTArray((0x64, 0x65, 0x66)))
        self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        self.assertEqual(remote_value.value, (100, 101, 102))

    def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueColorRGB(
            xknx,
            group_address=GroupAddress("1/2/3"))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTBinary(1))
            self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTArray((0x64, 0x65, 0x66, 0x67)))
            self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
