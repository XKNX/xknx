"""Unit test for Notification objects."""
from unittest.mock import AsyncMock, patch

import pytest
from xknx import XKNX
from xknx.devices import Notification
from xknx.dpt import DPTArray, DPTBinary, DPTString
from xknx.exceptions import CouldNotParseTelegram
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueWrite


@pytest.mark.asyncio
class TestNotification:
    """Test class for Notification object."""

    #
    # SYNC
    #
    async def test_sync_state(self):
        """Test sync function / sending group reads to KNX bus."""
        xknx = XKNX()
        notification = Notification(
            xknx, "Warning", group_address="1/2/3", group_address_state="1/2/4"
        )
        await notification.sync()
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/4"), payload=GroupValueRead()
        )

    #
    # TEST PROCESS
    #
    async def test_process(self):
        """Test process telegram with notification. Test if device was updated."""
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        telegram_set = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(DPTString().to_knx("Ein Prosit!"))),
        )
        await notification.process(telegram_set)
        assert notification.message == "Ein Prosit!"

        telegram_unset = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(DPTString().to_knx(""))),
        )
        await notification.process(telegram_unset)
        assert notification.message == ""

    async def test_process_callback(self):
        """Test process / reading telegrams from telegram queue. Test if callback was called."""

        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        after_update_callback = AsyncMock()
        notification.register_device_updated_cb(after_update_callback)

        telegram_set = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(DPTString().to_knx("Ein Prosit!"))),
        )
        await notification.process(telegram_set)
        after_update_callback.assert_called_with(notification)

    async def test_process_payload_invalid_length(self):
        """Test process wrong telegram (wrong payload length)."""
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((23, 24))),
        )
        with pytest.raises(CouldNotParseTelegram):
            await notification.process(telegram)

    async def test_process_wrong_payload(self):
        """Test process wrong telegram (wrong payload type)."""
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        with pytest.raises(CouldNotParseTelegram):
            await notification.process(telegram)

    #
    # TEST SET MESSAGE
    #
    async def test_set(self):
        """Test notificationing off notification."""
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        await notification.set("Ein Prosit!")
        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(DPTString().to_knx("Ein Prosit!"))),
        )
        # test if message longer than 14 chars gets cropped
        await notification.set("This is too long.")

        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray(DPTString().to_knx("This is too lo"))),
        )

    #
    # TEST DO
    #
    async def test_do(self):
        """Test 'do' functionality."""
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        await notification.do("message:Ein Prosit!")
        await xknx.devices.process(xknx.telegrams.get_nowait())
        assert notification.message == "Ein Prosit!"

    async def test_wrong_do(self):
        """Test wrong do command."""
        xknx = XKNX()
        notification = Notification(xknx, "Warning", group_address="1/2/3")
        with patch("logging.Logger.warning") as mock_warn:
            await notification.do("execute")
            mock_warn.assert_called_with(
                "Could not understand action %s for device %s", "execute", "Warning"
            )
        assert xknx.telegrams.qsize() == 0

    #
    # TEST has_group_address
    #
    def test_has_group_address(self):
        """Test has_group_address."""
        xknx = XKNX()
        notification = Notification(
            xknx, "Warning", group_address="1/2/3", group_address_state="1/2/4"
        )
        assert notification.has_group_address(GroupAddress("1/2/3"))
        assert notification.has_group_address(GroupAddress("1/2/4"))
        assert not notification.has_group_address(GroupAddress("2/2/2"))
