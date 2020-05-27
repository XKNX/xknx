"""Unit test for RemoteValueStep objects."""
import asyncio
import unittest

import pytest
pytestmark = pytest.mark.asyncio

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueStep
from xknx.telegram import GroupAddress, Telegram


class TestRemoteValueStep(unittest.TestCase):
    """Test class for RemoteValueStep objects."""

    def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx)
        self.assertEqual(remote_value.to_knx(RemoteValueStep.Direction.INCREASE), DPTBinary(1))
        self.assertEqual(remote_value.to_knx(RemoteValueStep.Direction.DECREASE), DPTBinary(0))

    def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx)
        self.assertEqual(remote_value.from_knx(DPTBinary(1)), RemoteValueStep.Direction.INCREASE)
        self.assertEqual(remote_value.from_knx(DPTBinary(0)), RemoteValueStep.Direction.DECREASE)

    def test_to_knx_invert(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx, invert=True)
        self.assertEqual(remote_value.to_knx(RemoteValueStep.Direction.INCREASE), DPTBinary(0))
        self.assertEqual(remote_value.to_knx(RemoteValueStep.Direction.DECREASE), DPTBinary(1))

    def test_from_knx_invert(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx, invert=True)
        self.assertEqual(remote_value.from_knx(DPTBinary(1)), RemoteValueStep.Direction.DECREASE)
        self.assertEqual(remote_value.from_knx(DPTBinary(0)), RemoteValueStep.Direction.INCREASE)

    def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueStep(xknx)
        with self.assertRaises(ConversionError):
            remote_value.to_knx(1)

    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueStep(
            xknx,
            group_address=GroupAddress("1/2/3"))
        await remote_value.decrease()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(0)))
        await remote_value.increase()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = xknx.telegrams.get_nowait()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(1)))

    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueStep(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTBinary(0))
        self.assertEqual(remote_value.value, None)
        await remote_value.process(telegram)
        self.assertEqual(remote_value.value, RemoteValueStep.Direction.DECREASE)

    async def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueStep(
            xknx,
            group_address=GroupAddress("1/2/3"))
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTArray((0x01)))
            await remote_value.process(telegram)
        with self.assertRaises(CouldNotParseTelegram):
            telegram = Telegram(
                group_address=GroupAddress("1/2/3"),
                payload=DPTBinary(3))
            await remote_value.process(telegram)
            # pylint: disable=pointless-statement
            remote_value.value
