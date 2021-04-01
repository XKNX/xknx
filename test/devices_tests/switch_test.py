"""Unit test for Switch objects."""
import asyncio
from unittest.mock import Mock, patch

import pytest
from xknx import XKNX
from xknx.devices import Switch
from xknx.dpt import DPTBinary
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite

from test.util import AsyncMock


# pylint: disable=no-self-use
@pytest.mark.asyncio
class TestSwitch:
    """Test class for Switch object."""

    #
    # SYNC
    #
    async def test_sync(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        switch = Switch(
            xknx, "TestOutlet", group_address_state="1/2/3", group_address="1/2/4"
        )
        await switch.sync()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"), payload=GroupValueRead()
        )

    async def test_sync_state_address(self):
        """Test sync function / sending group reads to KNX bus. Test with Switch with explicit state address."""
        xknx = XKNX()
        switch = Switch(
            xknx, "TestOutlet", group_address="1/2/3", group_address_state="1/2/4"
        )
        await switch.sync()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
        )

    #
    # TEST PROCESS
    #
    async def test_process(self):
        """Test process / reading telegrams from telegram queue. Test if device was updated."""
        xknx = XKNX()
        callback_mock = AsyncMock()

        switch1 = Switch(
            xknx, "TestOutlet", group_address="1/2/3", device_updated_cb=callback_mock
        )
        switch2 = Switch(
            xknx, "TestOutlet", group_address="1/2/3", device_updated_cb=callback_mock
        )
        assert switch1.state is None
        assert switch2.state is None
        callback_mock.assert_not_called()

        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        telegram_off = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

        await switch1.process(telegram_on)
        assert switch1.state is True
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        await switch1.process(telegram_off)
        assert switch1.state is False
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        # test setting switch2 to False with first telegram
        await switch2.process(telegram_off)
        assert switch2.state is False
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        await switch2.process(telegram_on)
        assert switch2.state is True
        callback_mock.assert_called_once()
        callback_mock.reset_mock()

    async def test_process_state(self):
        """Test process / reading telegrams from telegram queue. Test if device was updated."""
        xknx = XKNX()
        callback_mock = AsyncMock()

        switch1 = Switch(
            xknx,
            "TestOutlet",
            group_address="1/2/3",
            group_address_state="1/2/4",
            device_updated_cb=callback_mock,
        )
        switch2 = Switch(
            xknx,
            "TestOutlet",
            group_address="1/2/3",
            group_address_state="1/2/4",
            device_updated_cb=callback_mock,
        )
        assert switch1.state is None
        assert switch2.state is None
        callback_mock.assert_not_called()

        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueResponse(DPTBinary(1)),
        )
        telegram_off = Telegram(
            destination_address=GroupAddress("1/2/4"),
            payload=GroupValueResponse(DPTBinary(0)),
        )

        await switch1.process(telegram_on)
        assert switch1.state is True
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        await switch1.process(telegram_off)
        assert switch1.state is False
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        # test setting switch2 to False with first telegram
        await switch2.process(telegram_off)
        assert switch2.state is False
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        await switch2.process(telegram_on)
        assert switch2.state is True
        callback_mock.assert_called_once()
        callback_mock.reset_mock()

    async def test_process_invert(self):
        """Test process / reading telegrams from telegram queue with inverted switch."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3", invert=True)
        assert switch.state is None

        telegram_inv_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )
        telegram_inv_off = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        await switch.process(telegram_inv_on)
        assert switch.state is True
        await switch.process(telegram_inv_off)
        assert switch.state is False

    async def test_process_reset_after(self):
        """Test process reset_after."""
        xknx = XKNX()
        reset_after_sec = 0.001
        switch = Switch(
            xknx, "TestInput", group_address="1/2/3", reset_after=reset_after_sec
        )
        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

        await switch.process(telegram_on)
        assert switch.state
        assert xknx.telegrams.qsize() == 0
        await asyncio.sleep(reset_after_sec * 2)
        assert xknx.telegrams.qsize() == 1
        await switch.process(xknx.telegrams.get_nowait())
        assert not switch.state

    async def test_process_reset_after_cancel_existing(self):
        """Test process reset_after cancels existing reset tasks."""
        xknx = XKNX()
        reset_after_sec = 0.01
        switch = Switch(
            xknx, "TestInput", group_address="1/2/3", reset_after=reset_after_sec
        )
        telegram_on = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueResponse(DPTBinary(1)),
        )

        await switch.process(telegram_on)
        assert switch.state
        assert xknx.telegrams.qsize() == 0
        await asyncio.sleep(reset_after_sec / 2)
        # half way through the reset timer
        await switch.process(telegram_on)
        assert switch.state

        await asyncio.sleep(reset_after_sec / 2)
        assert xknx.telegrams.qsize() == 0

    async def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback was called."""
        # pylint: disable=no-self-use

        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")

        after_update_callback = Mock()

        async def async_after_update_callback(device):
            """Async callback."""
            after_update_callback(device)

        switch.register_device_updated_cb(async_after_update_callback)

        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        await switch.process(telegram)

        after_update_callback.assert_called_with(switch)

    #
    # TEST SET ON
    #
    async def test_set_on(self):
        """Test switching on switch."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        await switch.set_on()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

    #
    # TEST SET OFF
    #
    async def test_set_off(self):
        """Test switching off switch."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        await switch.set_off()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

    #
    # TEST SET INVERT
    #
    async def test_set_invert(self):
        """Test switching on/off inverted switch."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3", invert=True)

        await switch.set_on()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

        await switch.set_off()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )

    #
    # TEST DO
    #
    async def test_do(self):
        """Test 'do' functionality."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        await switch.do("on")
        await xknx.devices.process(xknx.telegrams.get_nowait())
        assert switch.state is True
        await switch.do("off")
        await xknx.devices.process(xknx.telegrams.get_nowait())
        assert switch.state is False

    async def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        with patch("logging.Logger.warning") as mock_warn:
            await switch.do("execute")
            mock_warn.assert_called_with(
                "Could not understand action %s for device %s", "execute", "TestOutlet"
            )
        assert xknx.telegrams.qsize() == 0

    #
    # TEST has_group_address
    #
    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        assert switch.has_group_address(GroupAddress("1/2/3"))
        assert not switch.has_group_address(GroupAddress("2/2/2"))

    #
    # TEST passive group addresses
    #
    def test_has_group_address_passive(self):
        """Test has_group_address with passive group address."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address=["1/2/3", "4/4/4"])
        assert switch.has_group_address(GroupAddress("1/2/3"))
        assert switch.has_group_address(GroupAddress("4/4/4"))
        assert not switch.has_group_address(GroupAddress("2/2/2"))

    async def test_process_passive(self):
        """Test process / reading telegrams from telegram queue. Test if device was updated."""
        xknx = XKNX()
        callback_mock = AsyncMock()

        switch1 = Switch(
            xknx,
            "TestOutlet",
            group_address=["1/2/3", "4/4/4"],
            group_address_state=["1/2/30", "5/5/5"],
            device_updated_cb=callback_mock,
        )
        assert switch1.state is None
        callback_mock.assert_not_called()

        telegram_on_passive = Telegram(
            destination_address=GroupAddress("4/4/4"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        telegram_off_passive = Telegram(
            destination_address=GroupAddress("5/5/5"),
            payload=GroupValueWrite(DPTBinary(0)),
        )

        await switch1.process(telegram_on_passive)
        assert switch1.state is True
        callback_mock.assert_called_once()
        callback_mock.reset_mock()
        await switch1.process(telegram_off_passive)
        assert switch1.state is False
        callback_mock.assert_called_once()
        callback_mock.reset_mock()

    def test_unique_id(self):
        """Test unique id functionality."""
        xknx = XKNX()
        switch = Switch(xknx, "TestOutlet", group_address="1/2/3")
        assert switch.unique_id == "1/2/3"
