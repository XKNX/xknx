"""Unit test for RemoteValueDpt2ByteUnsigned objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueDpt2ByteUnsigned
from xknx.telegram import GroupAddress, Telegram


class TestRemoteValueDptValue2Ucount(unittest.TestCase):
    """Test class for RemoteValueDpt2ByteUnsigned objects."""

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
        remote_value = RemoteValueDpt2ByteUnsigned(xknx)
        self.assertEqual(remote_value.to_knx(2571), DPTArray((0x0A, 0x0B)))

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueDpt2ByteUnsigned(xknx)
        self.assertEqual(remote_value.from_knx(DPTArray((0x0A, 0x0B))), 2571)

    def test_to_knx_error(self):
        """Test to_knx function with wrong parameters."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueDpt2ByteUnsigned(xknx)
        with self.assertRaises(ConversionError):
            remote_value.to_knx(65536)
        with self.assertRaises(ConversionError):
            remote_value.to_knx("a")

    def test_set(self):
        """Test setting value."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueDpt2ByteUnsigned(
            xknx,
            group_address=GroupAddress("1/2/3"))
        self.loop.run_until_complete(asyncio.Task(remote_value.set(2571)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTArray((0x0A, 0x0B))))
        self.loop.run_until_complete(asyncio.Task(remote_value.set(5500)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTArray((0x15, 0x7C, ))))

    def test_process(self):
        """Test process telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueDpt2ByteUnsigned(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTArray((0x0A, 0x0B)))
        self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        self.assertEqual(remote_value.value, 2571)

    def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueDpt2ByteUnsigned(
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
                payload=DPTArray((0x64, )))
            self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTArray((0x64, 0x53, 0x42, )))
            self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
