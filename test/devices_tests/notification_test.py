"""Unit test for Notification objects."""
from unittest.mock import AsyncMock, patch

from xknx import XKNX
from xknx.devices import Notification
from xknx.dpt import DPTArray, DPTBinary, DPTString
from xknx.telegram import GroupAddress, Telegram
from xknx.telegram.apci import GroupValueRead, GroupValueResponse, GroupValueWrite


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
            payload=GroupValueWrite(DPTString().to_knx("Ein Prosit!")),
        )
        await notification.process(telegram_set)
        assert notification.message == "Ein Prosit!"

        telegram_unset = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTString().to_knx("")),
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
            payload=GroupValueWrite(DPTString().to_knx("Ein Prosit!")),
        )
        await notification.process(telegram_set)
        after_update_callback.assert_called_with(notification)

    async def test_process_payload_invalid_length(self):
        """Test process wrong telegram (wrong payload length)."""
        xknx = XKNX()
        cb_mock = AsyncMock()
        notification = Notification(
            xknx, "Warning", group_address="1/2/3", device_updated_cb=cb_mock
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTArray((23, 24))),
        )
        with patch("logging.Logger.warning") as log_mock:
            await notification.process(telegram)
            log_mock.assert_called_once()
            cb_mock.assert_not_called()

    async def test_process_wrong_payload(self):
        """Test process wrong telegram (wrong payload type)."""
        xknx = XKNX()
        cb_mock = AsyncMock()
        notification = Notification(
            xknx, "Warning", group_address="1/2/3", device_updated_cb=cb_mock
        )
        telegram = Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTBinary(1)),
        )
        with patch("logging.Logger.warning") as log_mock:
            await notification.process(telegram)
            log_mock.assert_called_once()
            cb_mock.assert_not_called()

    #
    # TEST RESPOND
    #
    async def test_respond_to_read(self):
        """Test respond_to_read function."""
        xknx = XKNX()
        responding = Notification(
            xknx,
            "TestSensor1",
            group_address="1/1/1",
            respond_to_read=True,
            value_type="latin_1",
        )
        non_responding = Notification(
            xknx,
            "TestSensor2",
            group_address="1/1/1",
            respond_to_read=False,
            value_type="latin_1",
        )
        #  set initial payload of Notification
        responding.remote_value.value = "Halli Hallo"
        non_responding.remote_value.value = "Halli Hallo"

        read_telegram = Telegram(
            destination_address=GroupAddress("1/1/1"), payload=GroupValueRead()
        )
        # verify no response when respond_to_read is False
        await non_responding.process(read_telegram)
        assert xknx.telegrams.qsize() == 0

        # verify response when respond_to_read is True
        await responding.process(read_telegram)
        assert xknx.telegrams.qsize() == 1
        response = xknx.telegrams.get_nowait()
        assert response == Telegram(
            destination_address=GroupAddress("1/1/1"),
            payload=GroupValueResponse(
                DPTArray(
                    (
                        0x48,
                        0x61,
                        0x6C,
                        0x6C,
                        0x69,
                        0x20,
                        0x48,
                        0x61,
                        0x6C,
                        0x6C,
                        0x6F,
                        0x0,
                        0x0,
                        0x0,
                    ),
                ),
            ),
        )

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
            payload=GroupValueWrite(DPTString().to_knx("Ein Prosit!")),
        )
        # test if message longer than 14 chars gets cropped
        await notification.set("This is too long.")

        assert xknx.telegrams.qsize() == 1
        telegram = xknx.telegrams.get_nowait()
        assert telegram == Telegram(
            destination_address=GroupAddress("1/2/3"),
            payload=GroupValueWrite(DPTString().to_knx("This is too lo")),
        )

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
