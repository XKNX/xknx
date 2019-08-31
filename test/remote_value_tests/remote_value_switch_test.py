"""Unit test for RemoteValueSwitch objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueSwitch
from xknx.telegram import GroupAddress, Telegram


class TestRemoteValueSwitch(unittest.TestCase):
    """Test class for RemoteValueSwitch objects."""

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
        remote_value = RemoteValueSwitch(xknx)
        self.assertEqual(remote_value.to_knx(True), DPTBinary(True))
        self.assertEqual(remote_value.to_knx(False), DPTBinary(False))

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueSwitch(xknx)
        self.assertEqual(remote_value.from_knx(DPTBinary(True)), True)
        self.assertEqual(remote_value.from_knx(DPTBinary(0)), False)

    def test_to_knx_invert(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueSwitch(xknx, invert=True)
        self.assertEqual(remote_value.to_knx(True), DPTBinary(0))
        self.assertEqual(remote_value.to_knx(False), DPTBinary(1))

    def test_from_knx_invert(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueSwitch(xknx, invert=True)
        self.assertEqual(remote_value.from_knx(DPTBinary(1)), False)
        self.assertEqual(remote_value.from_knx(DPTBinary(0)), True)

    def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueSwitch(xknx)
        with self.assertRaises(ConversionError):
            remote_value.to_knx(1)

    def test_set(self):
        """Test setting value."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueSwitch(
            xknx,
            group_address=GroupAddress("1/2/3"))
        self.loop.run_until_complete(asyncio.Task(remote_value.on()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(1)))
        self.loop.run_until_complete(asyncio.Task(remote_value.off()))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(0)))

    def test_process(self):
        """Test process telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueSwitch(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTBinary(1))
        self.assertEqual(remote_value.value, None)
        self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        self.assertIsNotNone(remote_value.payload)
        self.assertEqual(remote_value.value, True)

    def test_process_off(self):
        """Test process OFF telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueSwitch(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTBinary(0))
        self.assertEqual(remote_value.value, None)
        self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        self.assertIsNotNone(remote_value.payload)
        self.assertEqual(remote_value.value, False)

    def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX(loop=self.loop)
        remote_value = RemoteValueSwitch(
            xknx,
            group_address=GroupAddress("1/2/3"))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTArray((0x01)))
            self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTBinary(3))
            self.loop.run_until_complete(asyncio.Task(remote_value.process(telegram)))
            # pylint: disable=pointless-statement
            remote_value.value
