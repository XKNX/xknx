"""Unit test for RemoteValueSwitch objects."""
import asyncio
import unittest

import pytest
pytestmark = pytest.mark.asyncio

from xknx import XKNX
from xknx.devices import RemoteValueSwitch
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.knx import DPTArray, DPTBinary, GroupAddress, Telegram


class TestRemoteValueSwitch(unittest.TestCase):
    """Test class for RemoteValueSwitch objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx)
        self.assertEqual(remote_value.to_knx(True), DPTBinary(True))
        self.assertEqual(remote_value.to_knx(False), DPTBinary(False))

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx)
        self.assertEqual(remote_value.from_knx(DPTBinary(True)), True)
        self.assertEqual(remote_value.from_knx(DPTBinary(0)), False)

    def test_to_knx_invert(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, invert=True)
        self.assertEqual(remote_value.to_knx(True), DPTBinary(0))
        self.assertEqual(remote_value.to_knx(False), DPTBinary(1))

    def test_from_knx_invert(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, invert=True)
        self.assertEqual(remote_value.from_knx(DPTBinary(1)), False)
        self.assertEqual(remote_value.from_knx(DPTBinary(0)), True)

    def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx)
        with self.assertRaises(ConversionError):
            remote_value.to_knx(1)

    def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(
            xknx,
            group_address=GroupAddress("1/2/3"))
        await asyncio.Task(remote_value.on())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(1)))
        await asyncio.Task(remote_value.off())
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(0)))

    def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTBinary(1))
        self.assertEqual(remote_value.value, None)
        await asyncio.Task(remote_value.process(telegram))
        self.assertIsNotNone(remote_value.payload)
        self.assertEqual(remote_value.value, True)

    def test_process_off(self):
        """Test process OFF telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTBinary(0))
        self.assertEqual(remote_value.value, None)
        await asyncio.Task(remote_value.process(telegram))
        self.assertIsNotNone(remote_value.payload)
        self.assertEqual(remote_value.value, False)

    def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(
            xknx,
            group_address=GroupAddress("1/2/3"))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTArray((0x01)))
            await asyncio.Task(remote_value.process(telegram))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTBinary(3))
            await asyncio.Task(remote_value.process(telegram))
            # pylint: disable=pointless-statement
            remote_value.value
