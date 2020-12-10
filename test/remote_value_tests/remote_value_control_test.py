"""Unit test for RemoteValueControl objects."""
import asyncio
import unittest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueControl
from xknx.telegram import GroupAddress, Telegram


class TestRemoteValueControl(unittest.TestCase):
    """Test class for RemoteValueControl objects."""

    def setUp(self):
        """Set up test class."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Tear down test class."""
        self.loop.close()

    def test_wrong_value_type(self):
        """Test initializing with wrong value_type."""
        xknx = XKNX()
        with self.assertRaises(ConversionError):
            RemoteValueControl(xknx, value_type="wrong_value_type")

    def test_valid_payload(self):
        """Test valid_payload method."""
        self.assertTrue(DPTBinary(0))
        self.assertTrue(DPTArray([0]))

    def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueControl(
            xknx, group_address=GroupAddress("1/2/3"), value_type="stepwise"
        )
        self.loop.run_until_complete(asyncio.Task(remote_value.set(25)))
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(destination_address=GroupAddress("1/2/3"), payload=DPTBinary(0xB)),
        )

    def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueControl(
            xknx, group_address=GroupAddress("1/2/3"), value_type="stepwise"
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"), payload=DPTBinary(0xB)
        )
        self.assertEqual(remote_value.value, None)
        self.loop.run_until_complete(remote_value.process(telegram))
        self.assertEqual(remote_value.value, 25)

    def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueControl(
            xknx, group_address=GroupAddress("1/2/3"), value_type="stepwise"
        )
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                destination_address=GroupAddress("1/2/3"), payload=DPTArray(0x01)
            )
            self.loop.run_until_complete(remote_value.process(telegram))
        with self.assertRaises(ConversionError):
            telegram = Telegram(
                destination_address=GroupAddress("1/2/3"), payload=DPTBinary(0x10)
            )
            self.loop.run_until_complete(remote_value.process(telegram))
            # pylint: disable=pointless-statement
            remote_value.value
