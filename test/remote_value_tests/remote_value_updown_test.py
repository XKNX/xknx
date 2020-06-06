"""Unit test for RemoteValueUpDown objects."""
import pytest

from xknx import XKNX
from xknx.dpt import DPTArray, DPTBinary
from xknx.exceptions import ConversionError, CouldNotParseTelegram
from xknx.remote_value import RemoteValueUpDown
from xknx.telegram import GroupAddress, Telegram

from xknx._test import Testcase

class TestRemoteValueUpDown(Testcase):
    """Test class for RemoteValueUpDown objects."""

    @pytest.mark.anyio
    async def test_to_knx(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx)
        self.assertEqual(remote_value.to_knx(RemoteValueUpDown.Direction.UP), DPTBinary(0))
        self.assertEqual(remote_value.to_knx(RemoteValueUpDown.Direction.DOWN), DPTBinary(1))

    @pytest.mark.anyio
    async def test_from_knx(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx)
        self.assertEqual(remote_value.from_knx(DPTBinary(0)), RemoteValueUpDown.Direction.UP)
        self.assertEqual(remote_value.from_knx(DPTBinary(1)), RemoteValueUpDown.Direction.DOWN)

    @pytest.mark.anyio
    async def test_to_knx_invert(self):
        """Test to_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx, invert=True)
        self.assertEqual(remote_value.to_knx(RemoteValueUpDown.Direction.UP), DPTBinary(1))
        self.assertEqual(remote_value.to_knx(RemoteValueUpDown.Direction.DOWN), DPTBinary(0))

    @pytest.mark.anyio
    async def test_from_knx_invert(self):
        """Test from_knx function with normal operation."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx, invert=True)
        self.assertEqual(remote_value.from_knx(DPTBinary(0)), RemoteValueUpDown.Direction.DOWN)
        self.assertEqual(remote_value.from_knx(DPTBinary(1)), RemoteValueUpDown.Direction.UP)

    @pytest.mark.anyio
    async def test_to_knx_error(self):
        """Test to_knx function with wrong parametern."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(xknx)
        with self.assertRaises(ConversionError):
            remote_value.to_knx(1)

    @pytest.mark.anyio
    async def test_set(self):
        """Test setting value."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(
            xknx,
            group_address=GroupAddress("1/2/3"))
        await remote_value.down()
        self.assertEqual(xknx.telegrams.qsize(), 1)
        telegram = await xknx.telegrams.get()
        self.assertEqual(
            telegram,
            Telegram(
                GroupAddress('1/2/3'),
                payload=DPTBinary(1)))
        await remote_value.up()
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
        remote_value = RemoteValueUpDown(
            xknx,
            group_address=GroupAddress("1/2/3"))
        telegram = Telegram(
            group_address=GroupAddress("1/2/3"),
            payload=DPTBinary(1))
        self.assertEqual(remote_value.value, None)
        await remote_value.process(telegram)
        self.assertEqual(remote_value.value, RemoteValueUpDown.Direction.DOWN)

    @pytest.mark.anyio
    async def test_to_process_error(self):
        """Test process errornous telegram."""
        xknx = XKNX()
        remote_value = RemoteValueUpDown(
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
