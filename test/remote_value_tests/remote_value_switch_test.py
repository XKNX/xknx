"""Unit test for RemoteValueSwitch objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueSwitch
from xknx.telegram import GroupAddress, Telegram

from xknx._test import Testcase

class TestRemoteValueSwitch(Testcase):
    """Test class for RemoteValueSwitch objects."""

    @pytest.mark.anyio
    async def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx)
        self.assertEqual(remote_value.to_knx(True), DPTBinary(True))
        self.assertEqual(remote_value.to_knx(False), DPTBinary(False))

    @pytest.mark.anyio
    async def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx)
        self.assertEqual(remote_value.from_knx(DPTBinary(True)), True)
        self.assertEqual(remote_value.from_knx(DPTBinary(0)), False)

    @pytest.mark.anyio
    async def test_to_knx_invert(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, invert=True)
        self.assertEqual(remote_value.to_knx(True), DPTBinary(0))
        self.assertEqual(remote_value.to_knx(False), DPTBinary(1))

    @pytest.mark.anyio
    async def test_from_knx_invert(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx, invert=True)
        self.assertEqual(remote_value.from_knx(DPTBinary(1)), False)
        self.assertEqual(remote_value.from_knx(DPTBinary(0)), True)

    @pytest.mark.anyio
    async def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(xknx)
        with self.assertRaises(ConversionError):
            remote_value.to_knx(1)

    @pytest.mark.anyio
    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(
            xknx,
            group_address=GroupAddress("1/2/3"))
        await remote_value.on()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = await xknx.telegrams.get()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(1)))
        await remote_value.off()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = await xknx.telegrams.get()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(0)))

    @pytest.mark.anyio
    async def test_process(self):
        """Test process telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTBinary(1))
        self.assertEqual(remote_value.value, None)
        await remote_value.process(telegram)
        self.assertIsNotNone(remote_value.payload)
        self.assertEqual(remote_value.value, True)

    @pytest.mark.anyio
    async def test_process_off(self):
        """Test process OFF telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTBinary(0))
        self.assertEqual(remote_value.value, None)
        await remote_value.process(telegram)
        self.assertIsNotNone(remote_value.payload)
        self.assertEqual(remote_value.value, False)

    @pytest.mark.anyio
    async def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueSwitch(
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
